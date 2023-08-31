---
title: process-syslogd-klogd
top: false
cover: false
toc: true
mathjax: true
date: 2023-08-31 11:32:30
password:
summary:
tags:
- linux
- process
categories:
- process
- linux
keywords:
description:
---

# syslog
"syslog" 是一个用于系统日志的标准化方法和系统，用于收集、存储和管理操作系统和应用程序的日志信息。在很多操作系统中，包括类Unix系统（如Linux），syslog是一个重要的组件，用于日志管理和故障排除。

关于 "syslog 线程" 的具体用途，这可能会因上下文和特定系统的设置而有所不同。一般来说，"syslog 线程" 可能指的是一个在系统中运行的线程，专门用于处理和管理日志消息。以下是一些可能的用途：

1. **日志收集和处理：** "syslog 线程" 可能会收集来自不同应用程序、服务和系统组件的日志消息。它可以对这些消息进行处理、分类和过滤，以确保将有关系统状态、故障和事件的相关信息记录下来。

2. **日志存储：** "syslog 线程" 可能会将日志消息存储到适当的位置，通常是日志文件。这些日志文件可能位于系统的标准位置，如 `/var/log` 目录下，或者根据系统管理员的配置而定。

3. **日志转发：** "syslog 线程" 通常还能够将日志消息转发到远程的日志服务器，以便集中管理和分析。这在大规模系统中特别有用，可以将日志从多个服务器和设备中集中处理。

4. **日志分析和监控：** "syslog 线程" 可能会涉及将日志消息传递给分析工具或监控系统，以便实时监视系统的健康状态、故障和异常情况。

总之，"syslog 线程" 在系统中起着重要作用，有助于捕获、管理和分析系统的日志信息，从而帮助管理员进行故障排除、安全监控和系统维护。

# syslog源码
/etc/rc5.d/S20syslog -> etc/init.d/syslog -> /etc/init.d/syslog.sysklogd
```shell
#! /bin/sh
# /etc/init.d/sysklogd: start the system log daemon.

### BEGIN INIT INFO
# Provides:             sysklogd
# Required-Start:       $remote_fs $time
# Required-Stop:        $remote_fs $time
# Should-Start:         $network
# Should-Stop:          $network
# Default-Start:        2 3 4 5
# Default-Stop:         0 1 6
# Short-Description:    System logger
### END INIT INFO

# Source function library.
. /etc/init.d/functions

PATH=/bin:/usr/bin:/sbin:/usr/sbin

pidfile_syslogd=/var/run/syslogd.pid
pidfile_klogd=/var/run/klogd.pid
binpath_syslogd=/sbin/syslogd
binpath_klogd=/sbin/klogd

test -x $binpath || exit 0

test ! -r /etc/default/syslogd || . /etc/default/syslogd

create_xconsole()
{
    # Only proceed if /dev/xconsole is used at all
    if ! grep -q '^[^#].*/dev/xconsole' /etc/syslog.conf
    then
	return
    fi

    if [ ! -e /dev/xconsole ]; then
	mknod -m 640 /dev/xconsole p
    else
	chmod 0640 /dev/xconsole
    fi
    chown root:adm /dev/xconsole
    test ! -x /sbin/restorecon || /sbin/restorecon /dev/xconsole
}

log_begin_msg () {
    echo -n $1
}

log_end_msg () {
    echo $1
}

log_success_msg () {
    echo $1
}

running()
{
    # No pidfile, probably no daemon present
    #
    if [ ! -f $pidfile ]
    then
	return 1
    fi

    pid=`cat $pidfile_syslogd`

    # No pid, probably no daemon present
    #
    if [ -z "$pid" ]
    then
	return 1
    fi

    if [ ! -d /proc/$pid ]
    then
	return 1
    fi

    cmd=`cat /proc/$pid/cmdline | tr "\000" "\n"|head -n 1`

    # No syslogd?
    #
    if [ "$cmd" != "$binpath" ]
    then
	return 1
    fi

    return 0
}

case "$1" in
  start)
    log_begin_msg "Starting system log daemon..."
    create_xconsole
    start-stop-daemon --start --quiet --pidfile $pidfile_syslogd --name syslogd --startas $binpath_syslogd -- $SYSLOGD
    log_end_msg $?
    log_begin_msg "Starting kernel log daemon..."
    start-stop-daemon --start --quiet --pidfile $pidfile_klogd --name klogd --startas $binpath_klogd -- $KLOGD
    log_end_msg $?
    ;;
  stop)
    log_begin_msg "Stopping system log daemon..."
    start-stop-daemon --stop --quiet --pidfile $pidfile_syslogd --name syslogd
    log_end_msg $?
    log_begin_msg "Stopping kernel log daemon..."
    start-stop-daemon --stop --quiet --retry 3 --exec $binpath_klogd --pidfile $pidfile_klogd
    log_end_msg $?
    ;;
  reload|force-reload)
    log_begin_msg "Reloading system log daemon..."
    start-stop-daemon --stop --quiet --signal 1 --pidfile $pidfile_syslogd --name syslogd
    log_end_msg $?
    log_begin_msg "Reloading kernel log daemon..."
    start-stop-daemon --stop --quiet --retry 3 --exec $binpath_klogd --pidfile $pidfile_klogd
    start-stop-daemon --start --quiet --pidfile $pidfile_klogd --name klogd --startas $binpath_klogd -- $KLOGD
    log_end_msg $?
    ;;
  restart)
    log_begin_msg "Restarting system log daemon..."
    start-stop-daemon --stop --retry 5 --quiet --pidfile $pidfile_syslogd --name syslogd
    start-stop-daemon --start --quiet --pidfile $pidfile_syslogd --name syslogd --startas $binpath_syslogd -- $SYSLOGD
    log_end_msg $?
    log_begin_msg "Reloading kernel log daemon..."
    start-stop-daemon --stop --quiet --retry 3 --exec $binpath_klogd --pidfile $pidfile_klogd
    start-stop-daemon --start --quiet --pidfile $pidfile_klogd --name klogd --startas $binpath_klogd -- $KLOGD
    log_end_msg $?
    ;;
  reload-or-restart)
    if running
    then
	$0 reload
    else
	$0 start
    fi
    ;;
  status)
    status syslogd
    RETVAL=$?
    status klogd
    rval=$?
    [ $RETVAL -eq 0 ] && exit $rval
    exit $RETVAL
    ;;
  *)
    log_success_msg "Usage: /etc/init.d/sysklogd {start|stop|reload|restart|force-reload|reload-or-restart|status}"
    exit 1
esac

exit 0
```
显而易见运行/sbin/syslogd和/sbin/klogd

# linux系统日志简介

Linux 日志系统是用于记录、存储和管理操作系统和应用程序的日志消息的机制和工具集合。日志是记录系统运行状态、事件、错误和其他相关信息的关键工具，对于故障排除、性能监控、安全审计和系统维护至关重要。以下是 Linux 日志系统的主要组成部分和概述：

1. **syslog：** Syslog 是一个标准化的日志消息传输协议和系统，用于将系统和应用程序的日志消息发送到集中的日志服务器或存储位置。Syslog 能够将日志消息分类、过滤和转发，并支持不同的日志级别，如调试、信息、警告和错误。

2. **日志消息级别：** Linux 日志消息通常分为几个不同的级别，例如：调试（debug）、信息（info）、警告（warning）、错误（error）和严重（critical）。这些级别帮助管理员快速了解日志的重要性。

3. **日志位置：** 在 Linux 系统中，日志消息通常存储在 `/var/log` 目录下。不同的服务和应用程序可能会有自己的日志文件，例如 `/var/log/messages`、`/var/log/syslog`、`/var/log/auth.log` 等。

4. **日志旋转：** 为了防止日志文件过大，Linux 系统通常使用日志旋转工具来定期归档、压缩或删除旧的日志文件，并创建新的日志文件。常见的日志旋转工具包括 `logrotate`。

5. **日志分析工具：** Linux 提供了各种用于分析和查看日志的工具，例如 `grep` 用于搜索、`tail` 用于实时查看、`less` 用于分页查看等。此外，还有更高级的工具如 `journalctl` 用于查看 Systemd Journal 日志。

6. **Systemd Journal：** Systemd 是现代 Linux 系统的初始化系统，它引入了 Systemd Journal，一个用于收集和管理系统日志的机制。`journalctl` 命令用于访问和查询 Systemd Journal 中的日志。

7. **远程日志：** Linux 日志系统支持将日志消息发送到远程的日志服务器，以便集中存储和分析。这对于大规模系统和分布式环境非常有用。

# 如何使用syslog和klog
[syslog官网](https://en.wikipedia.org/wiki/Syslog)
[klog官网](https://linux.die.net/man/8/klogd)
