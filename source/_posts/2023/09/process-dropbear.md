---
title: process-dropbear
top: false
cover: false
toc: true
mathjax: true
date: 2023-09-12 10:27:12
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

# dropbear线程
Dropbear是一个轻量级的SSH服务器和客户端程序，用于安全地远程访问和管理计算机系统。它被设计成非常小巧和高效，适用于资源受限的环境，如嵌入式系统和嵌入式设备。Dropbear是一个自由开源软件项目，通常在类似于Linux的操作系统中使用。

以下是Dropbear的一些主要特点和信息：

1. **轻量级和高效性能：** Dropbear的代码基础相对较小，这使得它在资源有限的系统上运行速度快，并占用较少的内存。

2. **SSH功能：** Dropbear提供了SSH服务器和客户端功能。SSH（Secure Shell）是一种加密的网络协议，用于在网络上安全地远程登录到其他计算机系统并执行命令。

3. **安全性：** Dropbear致力于提供强大的安全性。它支持现代的SSH协议，包括加密、认证和密钥管理，以确保通信的机密性和完整性。

4. **简化配置：** Dropbear的配置文件相对简单，易于管理。它通常具有类似于OpenSSH的配置选项，但具有更小的配置文件和更少的依赖项。

5. **适用于嵌入式系统：** Dropbear经常用于嵌入式系统、路由器和其他嵌入式设备，因为它占用的系统资源较少，且易于集成。

总的来说，Dropbear是一个小巧、高效且安全的SSH实现，适用于各种嵌入式和资源有限的环境，以提供安全的远程访问和管理功能。它与其他SSH服务器（如OpenSSH）功能相似，但更适合于需要小型、快速、低资源占用的用例。

# 移植
[dropbear官网](https://matt.ucc.asn.au/dropbear/dropbear.html)

## 软件下载

[zlib](http://www.zlib.net/)
[dropbear](http://matt.ucc.asn.au/dropbear/releases/)

## 软件编译
### zlib编译
1). 解压zlib：

    tar -zxvf zlib1.2.8.tar.gz -C /usr/local/zlib/src   (此处目录根据自己情况定义)

2). 进入zlib的解压目录

    cd /usr/local/zlib/src

3). 配置zlib

    ./configure --prefix=/usr/local/zlib  (即将zlib的库生成到该目录下)  

4). 上面步骤做完，将会生成Makefile，vim进去，修改Makefile

    CC=/home/qq/toolchain/bin/arm-openwrt-linux-gcc  //你交叉编译工具的绝对路径  
    AR=/home/qq/toolchain/bin/arm-openwrt-linux-gcc-ar  
    RANLIB=/home/qq/toolchain/bin/arm-openwrt-linux-gcc-ranlib    
    LDSHARED=/home/qq/toolchain/bin/arm-openwrt-linux-gcc -shared   -Wl,-soname,libz.so.1,--version-script,zlib.map   //(我只是将原来的gcc改成了我自己的编译工具，后面的参数没动过)

5). 执行make
6). 执行make install

完成以上步骤，你去/usr/local/zlib目录下看，会发现多了几个目录，代表zlib交叉编译成功！！

### dropbear编译
1). 解压dropbear：

    tar -jxvf dropbear-2016.74.tar.bz2 -C /usr/local/dropbear/src   //(此处目录根据自己情况定义)

2). 进入dropbear的解压目录

    cd /usr/local/dropbear/src

3). 配置dropbear

./configure --prefix=/usr/local/dropbear  --with-zlib=/usr/local/zlib/ CC=/home/qq/toolchain/bin/arm-openwrt-linux-gcc --host=arm  //(根据自己的情况修改)

4). 上面步骤做完，Makefile内的CC会自动修改掉，不用再人为修改Makefile了
5). 执行make

    make PROGRAMS="dropbear dbclient dropbearkey dropbearconvert scp" 

6). 执行make install

    make PROGRAMS="dropbear dbclient dropbearkey dropbearconvert scp" install

7). 注意，因为默认不编译scp，PROGRAMS=xxx是强制编译出scp来，不这样干也可以，但是需要自己生成scp：

    make scp  
    cp scp /usr/local/dropbear

完成以上步骤，你去/usr/local/dropbear目录下看，会发现多了几个目录，代表dropbear交叉编译成功！！

# 移植文件到开发板上

    将/usr/local/dropbear/bin/移植到板卡的/usr/bin/下；
    将/usr/local/dropbear/sbin/下的文件都复制到板卡的/usr/sbin/目录下

```shell
root@ATK-IMX6U:/usr/sbin# ls -l | grep drop*
Binary file dropbearconvert matches
Binary file dropbearkey matches
Binary file dropbearmulti matches

root@ATK-IMX6U:/usr/bin# ls -l | grep drop*
-rwxr-xr-x   1 root root  19K Jul 20 10:22 apt-cdrom
lrwxrwxrwx   1 root root   23 Jan  1  1970 dbclient -> /usr/sbin/dropbearmulti
lrwxrwxrwx   1 root root   23 Jan  1  1970 scp -> /usr/sbin/dropbearmulti
lrwxrwxrwx   1 root root   23 Jan  1  1970 ssh -> /usr/sbin/dropbearmulti
```

# 配置开机启动
在etc/rc5.d中创建链接文件指向../init.d/dropbear
```shell
ln -s /etc/init.d/dropbear /etc/rc5.d/S10dropbear
```
```shell
root@ATK-IMX6U:/etc/rc5.d# ls -l | grep dro*
lrwxrwxrwx 1 root root 18 Jan  1  1970 S10dropbear -> ../init.d/dropbear
```
在etc/init.d中创建dropbear文件
```shell
#!/bin/sh
### BEGIN INIT INFO
# Provides:           sshd
# Required-Start:     $remote_fs $syslog $networking
# Required-Stop:      $remote_fs $syslog
# Default-Start:      2 3 4 5
# Default-Stop:       1
# Short-Description:  Dropbear Secure Shell server
### END INIT INFO
#
# Do not configure this file. Edit /etc/default/dropbear instead!
# 请不要直接编辑此文件，请编辑 /etc/default/dropbear 文件来配置Dropbear服务。

# 设置PATH环境变量，指定脚本执行时可执行文件的搜索路径
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# Dropbear可执行文件的路径
DAEMON=/usr/sbin/dropbear

# 服务的名称
NAME=dropbear

# 服务的描述
DESC="Dropbear SSH server"

# 保存Dropbear进程的PID的文件路径
PIDFILE=/var/run/dropbear.pid

# Dropbear监听的SSH端口，默认是22
DROPBEAR_PORT=22

# Dropbear附加参数，默认为空
DROPBEAR_EXTRA_ARGS=

# 是否禁止启动Dropbear服务的标志，0表示不禁止
NO_START=0

set -e

test ! -r /etc/default/dropbear || . /etc/default/dropbear
test "$NO_START" = "0" || exit 0
test -x "$DAEMON" || exit 0
test ! -h /var/service/dropbear || exit 0

# 设置一个标志，用于检测文件系统是否为只读（readonly_rootfs=0表示不是只读）
readonly_rootfs=0
for flag in `awk '{ if ($2 == "/") { split($4,FLAGS,",") } }; END { for (f in FLAGS) print FLAGS[f] }' </proc/mounts`; do
  case $flag in
   ro)
     readonly_rootfs=1
     ;;
  esac
done

# 根据文件系统是否只读，设置Dropbear的密钥文件路径
if [ $readonly_rootfs = "1" ]; then
  mkdir -p /var/lib/dropbear
  DROPBEAR_RSAKEY_DEFAULT="/var/lib/dropbear/dropbear_rsa_host_key"
  DROPBEAR_DSSKEY_DEFAULT="/var/lib/dropbear/dropbear_dss_host_key"
else
  DROPBEAR_RSAKEY_DEFAULT="/etc/dropbear/dropbear_rsa_host_key"
  DROPBEAR_DSSKEY_DEFAULT="/etc/dropbear/dropbear_dss_host_key"
fi

# 如果用户配置了DROPBEAR_BANNER，将其添加到Dropbear附加参数中
test -z "$DROPBEAR_BANNER" || \
  DROPBEAR_EXTRA_ARGS="$DROPBEAR_EXTRA_ARGS -b $DROPBEAR_BANNER"

# 如果用户没有配置DROPBEAR_RSAKEY，默认使用DROPBEAR_RSAKEY_DEFAULT
test -n "$DROPBEAR_RSAKEY" || \
  DROPBEAR_RSAKEY=$DROPBEAR_RSAKEY_DEFAULT

# 如果用户没有配置DROPBEAR_DSSKEY，默认使用DROPBEAR_DSSKEY_DEFAULT
test -n "$DROPBEAR_DSSKEY" || \
  DROPBEAR_DSSKEY=$DROPBEAR_DSSKEY_DEFAULT

# 如果用户没有配置DROPBEAR_KEYTYPES，默认使用"rsa"作为密钥类型
test -n "$DROPBEAR_KEYTYPES" || \
  DROPBEAR_KEYTYPES="rsa"

# 生成Dropbear密钥
gen_keys() {
for t in $DROPBEAR_KEYTYPES; do
  case $t in
    rsa)
        if [ -f "$DROPBEAR_RSAKEY" -a ! -s "$DROPBEAR_RSAKEY" ]; then
                rm $DROPBEAR_RSAKEY || true
        fi
        test -f $DROPBEAR_RSAKEY || dropbearkey -t rsa -f $DROPBEAR_RSAKEY
	;;
    dsa)
        if [ -f "$DROPBEAR_DSSKEY" -a ! -s "$DROPBEAR_DSSKEY" ]; then
                rm $DROPBEAR_DSSKEY || true
        fi
        test -f $DROPBEAR_DSSKEY || dropbearkey -t dss -f $DROPBEAR_DSSKEY
	;;
  esac
done
}

# 根据启动参数执行不同的操作
case "$1" in
  start)
    echo -n "Starting $DESC: "
    gen_keys
    KEY_ARGS=""
    test -f $DROPBEAR_DSSKEY && KEY_ARGS="$KEY_ARGS -d $DROPBEAR_DSSKEY"
    test -f $DROPBEAR_RSAKEY && KEY_ARGS="$KEY_ARGS -r $DROPBEAR_RSAKEY"
    start-stop-daemon -S -p $PIDFILE \
      -x "$DAEMON" -- $KEY_ARGS \
        -p "$DROPBEAR_PORT" $DROPBEAR_EXTRA_ARGS
    echo "$NAME."
    ;;
  stop)
    echo -n "Stopping $DESC: "
    start-stop-daemon -K -x "$DAEMON" -p $PIDFILE
    echo "$NAME."
    ;;
  restart|force-reload)
    echo -n "Restarting $DESC: "
    start-stop-daemon -K -x "$DAEMON" -p $PIDFILE
    sleep 1
    KEY_ARGS=""
    test -f $DROPBEAR_DSSKEY && KEY_ARGS="$KEY_ARGS -d $DROPBEAR_DSSKEY"
    test -f $DROPBEAR_RSAKEY && KEY_ARGS="$KEY_ARGS -r $DROPBEAR_RSAKEY"
    start-stop-daemon -S -p $PIDFILE \
      -x "$DAEMON" -- $KEY_ARGS \
        -p "$DROPBEAR_PORT" $DROPBEAR_EXTRA_ARGS
    echo "$NAME."
    ;;
  *)
    N=/etc/init.d/$NAME
    echo "Usage: $N {start|stop|restart|force-reload}" >&2
    exit 1
    ;;
esac

exit 0

```

# dropbear使用
[dhclient命令](https://linux265.com/course/linux-command-dhclient.html)
[scp命令](https://linux265.com/course/linux-command-scp.html)
[SSH命令](https://linux265.com/news/2283.html)
这三命令都是dropbearmulti参数
/usr/sbin中有 `dropbearmulti`、`dropbearkey` 和 `dropbearconvert` 是与 Dropbear 相关的辅助工具，用于不同的任务, 都是由dropbear编译生成的.

1. **dropbearmulti**：

   `dropbearmulti` 是 Dropbear 的多实例执行工具。它允许在同一系统上运行多个 Dropbear SSH 服务器实例，每个实例可以监听不同的端口、使用不同的密钥等配置。这对于需要同时提供多个 SSH 服务的情况很有用，例如，一个服务器可以监听默认的 SSH 端口 22，而另一个实例可以监听另一个自定义的端口，以提供额外的安全性。

2. **dropbearkey**：

   `dropbearkey` 是 Dropbear 的密钥生成工具。它用于生成 SSH 密钥对，包括 RSA 和 DSA 密钥。这些密钥对用于身份验证和数据加密，是建立安全 SSH 连接所必需的组成部分。`dropbearkey` 可以用于生成服务器的主机密钥和用户的身份验证密钥。

3. **dropbearconvert**：

   `dropbearconvert` 是 Dropbear 的密钥格式转换工具。它用于将不同格式的 SSH 密钥（如 OpenSSH 格式）转换为 Dropbear 可以识别的格式。这对于在不同 SSH 服务器之间迁移密钥或在不同格式的密钥之间进行转换很有用。例如，如果你有一个 OpenSSH 格式的密钥，但想在 Dropbear 上使用，你可以使用 `dropbearconvert` 来转换它。

这些工具通常与 Dropbear 一起提供，并在配置和管理 SSH 服务器时非常有用。它们使用户能够生成、管理和迁移 SSH 密钥，以及配置多个 Dropbear SSH 服务器实例，以满足不同的需求。
