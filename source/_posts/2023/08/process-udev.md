---
title: process-udev
top: false
cover: false
toc: true
mathjax: true
date: 2023-08-28 17:18:24
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

# udev
`udev`（用户空间设备管理器）是用于管理 Linux 内核设备和设备事件的守护进程。它的主要目的是在系统中自动检测硬件设备的插入、拔出等事件，并根据这些事件进行相应的设备管理操作，例如加载适当的驱动程序、创建设备节点、设置权限等。

`udev` 本质上是一个守护进程，它会监听内核发送的事件（例如设备插入、拔出、属性变化等），并采取适当的措施来管理这些设备。为了实现这一功能，`udev` 使用了多线程技术。其中，`udev` 线程的主要任务包括：

1. **事件监听：** `udev` 线程会监听内核发送的设备事件，例如设备的插入或拔出。

2. **事件处理：** 一旦接收到设备事件，`udev` 线程会根据事件的类型和属性执行相应的处理操作。这可能涉及到加载驱动程序、创建设备文件、设置设备权限等。

3. **规则执行：** `udev` 使用规则来描述设备的管理操作。当设备事件发生时，`udev` 线程会根据预定义的规则来判断需要执行哪些操作。

4. **设备节点管理：** `udev` 线程会负责在 `/dev` 目录下创建和管理设备节点文件，这些文件用于与用户空间应用程序进行通信。

5. **热插拔支持：** `udev` 线程使系统能够自动识别硬件的热插拔操作，并在设备插入或拔出时自动执行相应的管理操作。

6. **属性处理：** `udev` 可以从设备的属性信息中获取有关设备的信息，并在必要时将这些属性信息用于设备管理操作。

# udevd程序
## BusyBox 构建根文件系统
BusyBox中具有udev的功能，生成文件系统的时候在sbin/中生成了udev
## udev移植
从udev下载网址可以下载到udev的源码。下面为移植步骤。

    下载udev源码包，并解压
    修改Makefile中的CROSS交叉编译工具为自己开发板的编译器
    执行make进行编译。
    然后执行strip udev uded udevstart udevinfo udevtest。并将这些文件拷贝到rootfs/sbin目录下。
    添加对udev的支持，修改/etc/init.d/rcS脚本，添加如下命令：

```c
root@ATK-IMX6U:/sbin# ls -ll | grep udev                                        
lrwxrwxrwx 1 root root       16 Jun 10 18:21 udevadm -> /usr/bin/udevadm
-rwxr-xr-x 1 root root     239K Jul 20  2021 udevd
```

# udevd如何被运行
根据[init线程启动/etc/inittab](https://qian-qiang.github.io/2023/08/process-init.html)可知会先执行si::sysinit:/etc/init.d/rcS文件的启动脚本

```c
...................
# Boot-time system configuration/initialization script.
# This is run first except when booting in emergency (-b) mode.
si::sysinit:/etc/init.d/rcS

....................
```
```c
root@ATK-IMX6U:/etc/rcS.d# ls -ll
total 0
lrwxrwxrwx 1 root root 20 Jun 10 18:21 S00psplash.sh -> ../init.d/psplash.sh
lrwxrwxrwx 1 root root 19 Jun 10 18:21 S02banner.sh -> ../init.d/banner.sh
lrwxrwxrwx 1 root root 18 Jun 10 18:21 S02sysfs.sh -> ../init.d/sysfs.sh
lrwxrwxrwx 1 root root 21 Jun 10 18:21 S03mountall.sh -> ../init.d/mountall.sh
lrwxrwxrwx 1 root root 14 Jun 10 18:21 S04udev -> ../init.d/udev
lrwxrwxrwx 1 root root 21 Jun 10 18:21 S05modutils.sh -> ../init.d/modutils.sh
lrwxrwxrwx 1 root root 22 Jun 10 18:21 S06alignment.sh -> ../init.d/alignment.sh
lrwxrwxrwx 1 root root 22 Jun 10 18:21 S06checkroot.sh -> ../init.d/checkroot.sh
lrwxrwxrwx 1 root root 18 Jun 10 18:21 S07bootlogd -> ../init.d/bootlogd
lrwxrwxrwx 1 root root 34 Jun 10 18:21 S29read-only-rootfs-hook.sh -> ../init.d/read-only-rootfs-hook.sh
lrwxrwxrwx 1 root root 20 Jun 10 18:21 S36udev-cache -> ../init.d/udev-cache
lrwxrwxrwx 1 root root 30 Jun 10 18:21 S37populate-volatile.sh -> ../init.d/populate-volatile.sh
lrwxrwxrwx 1 root root 19 Jun 10 18:21 S38devpts.sh -> ../init.d/devpts.sh
lrwxrwxrwx 1 root root 18 Jun 10 18:21 S38dmesg.sh -> ../init.d/dmesg.sh
lrwxrwxrwx 1 root root 17 Jun 10 18:21 S38urandom -> ../init.d/urandom
lrwxrwxrwx 1 root root 20 Jun 10 18:21 S39alsa-state -> ../init.d/alsa-state
lrwxrwxrwx 1 root root 21 Jun 10 18:21 S39hostname.sh -> ../init.d/hostname.sh
lrwxrwxrwx 1 root root 21 Jun 10 18:21 S55bootmisc.sh -> ../init.d/bootmisc.sh
```
启动了../init.d/udev脚本

```shell
#!/bin/sh

### BEGIN INIT INFO
# Provides:          udev
# Required-Start:    mountvirtfs
# Required-Stop:     
# Default-Start:     S
# Default-Stop:
# Short-Description: Start udevd, populate /dev and load drivers.
### END INIT INFO

export TZ=/etc/localtime

#检查是否存在 /sys/class 目录
[ -d /sys/class ] || exit 1
#检查 /proc/mounts 文件是否可读
[ -r /proc/mounts ] || exit 1
#检查 /sbin/udevd 是否可执行
[ -x /sbin/udevd ] || exit 1

# 路径到缓存的udev系统配置文件
SYSCONF_CACHED="/etc/udev/cache.data"

# 路径到临时的udev系统配置文件
SYSCONF_TMP="/dev/shm/udev.cache"

# 用于请求缓存重新生成的标记文件的路径
DEVCACHE_REGEN="/dev/shm/udev-regen" # 创建以请求缓存重新生成

# 用作判断是否可以重新使用udev缓存的文件列表
CMP_FILE_LIST="/proc/version /proc/cmdline /proc/devices"
[ -f /proc/atags ] && CMP_FILE_LIST="$CMP_FILE_LIST /proc/atags"

# 包含在缓存的系统状态中的文件的元数据（大小/修改时间/名称）的列表
META_FILE_LIST="lib/udev/rules.d/* etc/udev/rules.d/*"

# 用于计算系统配置的命令函数
sysconf_cmd () {
	cat -- $CMP_FILE_LIST        # 打印 CMP_FILE_LIST 中的文件内容
	stat -c '%s %Y %n' -- $META_FILE_LIST | awk -F/ '{print $1 " " $NF;}'  # 打印 META_FILE_LIST 中文件的元数据信息
}


[ -f /etc/default/udev-cache ] && . /etc/default/udev-cache
[ -f /etc/udev/udev.conf ] && . /etc/udev/udev.conf
[ -f /etc/default/rcS ] && . /etc/default/rcS

# 终止正在运行的 udevd 进程的函数
kill_udevd () {
    pid=`pidof -x udevd`     # 获取 udevd 进程的 PID
    [ -n "$pid" ] && kill $pid  # 如果 PID 存在，则使用 kill 命令终止进程
}

case "$1" in
  start)
    export ACTION=add
    # propagate /dev from /sys
    echo "Starting udev"

    # 在尝试启动 udev 之前，检查是否已加载了所需的 devtmpfs 文件系统，
    # 如果未加载，则输出错误信息并停止系统。
    if ! grep -q devtmpfs /proc/filesystems; then
        echo "Missing devtmpfs, which is required for udev to run";
        echo "Halting..."
        halt
    fi

    # 如果尚未完成，在 /dev 上挂载 devtmpfs 文件系统
    # 使用 LANG=C awk 来查找 /proc/mounts 文件中是否已挂载了 /dev 目录的 devtmpfs 文件系统。
    # 如果找到，则退出状态为 1（表示没有找到），执行下面的花括号中的命令块。
    LANG=C awk '$2 == "/dev" && ($3 == "devtmpfs") { exit 1 }' /proc/mounts && {
        mount -n -o mode=0755 -t devtmpfs none "/dev"
    }

    # 如果 /dev/pts 不存在，则创建它，并设置权限为 0755。
    [ -e /dev/pts ] || mkdir -m 0755 /dev/pts

    # 如果 /dev/shm 不存在，则创建它，并设置权限为 1777。
    [ -e /dev/shm ] || mkdir -m 1777 /dev/shm

    # 为了满足 udev 的自动挂载规则，需要确保 /var/volatile/tmp 目录可用。
    # 因为 /tmp 是一个符号链接到 /var/tmp，而 /var/tmp 又是一个符号链接到 /var/volatile/tmp，
    # 所以需要确保 /var/volatile/tmp 目录存在。
    mkdir -m 1777 -p /var/volatile/tmp


    # Cache handling.
    #DEVCACHE udev缓存我没使用不分析
    if [ "$DEVCACHE" != "" ]; then
            if [ -e $DEVCACHE ]; then
		    sysconf_cmd > "$SYSCONF_TMP"
		    if cmp $SYSCONF_CACHED $SYSCONF_TMP >/dev/null; then
                            tar xmf $DEVCACHE -C / -m
                            not_first_boot=1
                            [ "$VERBOSE" != "no" ] && echo "udev: using cache file $DEVCACHE"
                            [ -e $SYSCONF_TMP ] && rm -f "$SYSCONF_TMP"
                            [ -e "$DEVCACHE_REGEN" ] && rm -f "$DEVCACHE_REGEN"
                    else
			    # Output detailed reason why the cached /dev is not used
			    cat <<EOF
udev: Not using udev cache because of changes detected in the following files:
udev:     $CMP_FILE_LIST
udev:     $META_FILE_LIST
udev: The udev cache will be regenerated. To identify the detected changes,
udev: compare the cached sysconf at   $SYSCONF_CACHED
udev: against the current sysconf at  $SYSCONF_TMP
EOF
			    touch "$DEVCACHE_REGEN"
                    fi
	    else
		    if [ "$ROOTFS_READ_ONLY" != "yes" ]; then
			    # If rootfs is not read-only, it's possible that a new udev cache would be generated;
			    # otherwise, we do not bother to read files.
			    touch "$DEVCACHE_REGEN"
		    fi
            fi
    fi

    # make_extra_nodes
    # kill_udevd 函数用于终止 udevd 进程。在设备节点创建完成后，通常需要重新加载或者重启  # udevd 进程，以便它可以正确地识别和处理新增的设备。终止 udevd 进程后，它会重新启动并重新# 加载规则和配置，以适应新增的设备情况
    kill_udevd > "/dev/null" 2>&1

    # trigger the sorted events
    # 这个文件通常用于指定在设备事件发生时要执行的热插拔处理程序（hotplug handler）。如果该文# 件存在，会将一个空字符写入该文件，这实际上是在通知系统要开始处理设备事件
    [ -e /proc/sys/kernel/hotplug ] && echo -e '\000' >/proc/sys/kernel/hotplug
    # 这行代码启动 udevd 进程，参数 -d 表示以调试模式启动
    /sbin/udevd -d

    #这段代码是在设备事件触发后进行一系列的操作，以确保设备管理系统（udev）适当地处理新添加的设备
    udevadm control --env=STARTUP=1
    if [ "$not_first_boot" != "" ];then
            if [ "$PROBE_PLATFORM_BUS" != "yes" ]; then
                PLATFORM_BUS_NOMATCH="--subsystem-nomatch=platform"
            else
                PLATFORM_BUS_NOMATCH=""
            fi
            udevadm trigger --action=add --subsystem-nomatch=tty --subsystem-nomatch=mem --subsystem-nomatch=vc --subsystem-nomatch=vtconsole --subsystem-nomatch=misc --subsystem-nomatch=dcon --subsystem-nomatch=pci_bus --subsystem-nomatch=graphics --subsystem-nomatch=backlight --subsystem-nomatch=video4linux $PLATFORM_BUS_NOMATCH
            (udevadm settle --timeout=3; udevadm control --env=STARTUP=)&
    else
            udevadm trigger --action=add
            udevadm settle
    fi
    ;;
  stop)
    echo "Stopping udevd"
    start-stop-daemon --stop --name udevd --quiet
    ;;
  restart)
    $0 stop
    sleep 1
    $0 start
    ;;
  status)
    pid=`pidof -x udevd`
    if [ -n "$pid" ]; then
	echo "udevd (pid $pid) is running ..."
    else
	echo "udevd is stopped"
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|status|restart}"
    exit 1
esac
exit 0
```

# udevd使用方法
[使用方法](https://linux.die.net/man/7/udev)

## 配置文件-/etc/udev/udev.conf

udev expects its main configuration file at /etc/udev/udev.conf. It consists of a set of variables allowing the user to override default udev values. The following variables can be set:
udev 的主要配置文件位于 /etc/udev/udev.conf。它由一组变量组成，允许用户覆盖默认的 udev 值。可以设置以下变量： 

udev_root
    Specifies where to place the device nodes in the filesystem. The default value is /dev. 
    指定在文件系统中放置设备节点的位置。默认值为/dev。 
udev_log
    The logging priority. Valid values are the numerical syslog priorities or their textual representations: err, info and debug. 
    记录优先级。有效值为数字系统日志优先级或其文本表示：err、info和debug。

```shell
root@ATK-IMX6U:/etc/udev# cat udev.conf 
# see udev.conf(5) for details
udev_root"/dev/"
udev_log="info"
udev_rules="/etc/udev/rules.d/"
```

## 规则文件-/etc/udev/rules.d/
规则文件存放在udev_rules指定的目录下，并且文件名的后缀为.lures。规则文件可能有多个，匹配的先后顺序是安装ASCII码来进行的。如找到了比配的规则，则暂停匹配，不在去匹配后续的规则文件。所以自定义的规则文件基本上都是以数字开头，这样提高了规则文件的优先级。下图是简单的规则文件规则文件以行为单位，一行就是一条规则

### udev规则所有操作符
    “==”：　　比较键、值，若等于，则该条件满足；
    “!=”： 　　比较键、值，若不等于，则该条件满足；
    “=”： 　　 对一个键赋值；
    “+=”：　　为一个表示多个条目的键赋值。
    “:=”：　　对一个键赋值，并拒绝之后所有对该键的改动。目的是防止后面的规则文件对该键赋值。

### udev规则的匹配键
    ACTION： 　　 　　　事件 (uevent) 的行为，例如：add( 添加设备 )、remove( 删除设备 )。
    KERNEL： 　　 　　　内核设备名称，例如：sda, cdrom。
    DEVPATH：　　　　　 设备的 devpath 路径。
    SUBSYSTEM： 　　　　设备的子系统名称，例如：sda 的子系统为 block。
    BUS： 　　　　　　　 设备在 devpath 里的总线名称，例如：usb。
    DRIVER： 　　　　 　设备在 devpath 里的设备驱动名称，例如：ide-cdrom。
    ID： 　　　　　　　  设备在 devpath 里的识别号。
    SYSFS{filename}： 设备的 devpath 路径下，设备的属性文件“filename”里的内容。例如：   SYSFS{model}==“ST936701SS”表示：如果设备的型号为 ST936701SS，则该设备匹配该匹配键。
    
    ENV{key}： 　　　　环境变量。在一条规则中，可以设定最多五条环境变量的 匹配键。
    PROGRAM：　　　　　调用外部命令。
    RESULT： 　　　　　外部命令 PROGRAM 的返回结果。

### udev的重要赋值键
    NAME： 　在 /dev下产生的设备文件名。只有第一次对某个设备的 NAME 的赋值行为生效，之后匹配的规则再对该设备的 NAME 赋值行为将被忽略。如果没有任何规则对设备的 NAME 赋值，udev 将使用内核设备名称来产生设备文件。
    SYMLINK：　 为 /dev/下的设备文件产生符号链接。由于 udev 只能为某个设备产生一个设备文件，所以为了不覆盖系统默认的 udev 规则所产生的文件，推荐使用符号链接。
    OWNER, GROUP, MODE：　　为设备设定权限。
    ENV{key}：　　　　　　　　　导入一个环境变量。

### udev的值和可调用的替换操作符
    $kernel, %k：　　　　　　　　设备的内核设备名称，例如：sda、cdrom。
    $number, %n：　　　　　　　 设备的内核号码，例如：sda3 的内核号码是 3。
    $devpath, %p：　　　　　　　设备的 devpath路径。
    $id, %b：　　　　　　　　　　设备在 devpath里的 ID 号。
    $sysfs{file}, %s{file}：　　 设备的 sysfs里 file 的内容。其实就是设备的属性值。
    $env{key}, %E{key}：　　　 一个环境变量的值。
    $major, %M：　　　　　　　　设备的 major 号。
    $minor %m：　　　　　　　　设备的 minor 号。
    $result, %c：　　　　　　　　PROGRAM 返回的结果。
    $parent, %P：　　　　　　 父设备的设备文件名。
    $root, %r：　　　　　　　　 udev_root的值，默认是 /dev/。
    $tempnode, %N：　　　　　　临时设备名。
    %%：　　　　　　　　　　　　符号 % 本身。
    $$：　　　　　　　　　　　　　符号 $ 本身。

```shell
root@ATK-IMX6U:/etc/udev/rules.d# ls
10-imx.rules         55-hpmud.rules              60-sysprof.rules        automount.rules   local.rules
40-libgphoto2.rules  56-hpmud_add_printer.rules  80-net-name-slot.rules  autonet.rules
50-firmware.rules    56-hpmud_support.rules      86-hpmud_plugin.rules   localextra.rules
root@ATK-IMX6U:/etc/udev/rules.d# cat 10-imx.rules 
# Create symlinks for i.mx keypads and touchscreens
#SUBSYSTEM=="input" KERNEL=="event*" ATTRS{name}=="mxckpd",     SYMLINK+="input/keyboard0"
#SUBSYSTEM=="input" KERNEL=="event*" ATTRS{name}=="mxc_ts",     SYMLINK+="input/ts0"
#SUBSYSTEM=="input" KERNEL=="event*" ATTRS{name}=="imx_adc_ts", SYMLINK+="input/ts0"
#SUBSYSTEM=="input" KERNEL=="event*" ATTRS{name}=="mpr084",     SYMLINK+="input/keyboard0"
#SUBSYSTEM=="input" KERNEL=="event*" ATTRS{name}=="tsc2007",    SYMLINK+="input/ts0"
#SUBSYSTEM=="input" KERNEL=="event*" ATTRS{name} =="STMP3XXX touchscreen",    SYMLINK+="input/ts0"
#SUBSYSTEM=="input" KERNEL=="event*" ATTRS{name} =="MXS touchscreen",    SYMLINK+="input/ts0"
#SUBSYSTEM=="input" KERNEL=="event*" ATTRS{name} =="HannStar P1003 Touchscreen",        SYMLINK+="input/ts0"
#SUBSYSTEM=="input" KERNEL=="event*" ATTRS{name} =="eGalax Touch Screen",       SYMLINK+="input/ts0"

# The long class name gets cut off to be mc13783_connectiv in 
# /sys/class/mc13783_connectivity/mc13783_connectivit
KERNEL=="mc13783_connectiv*",  NAME="mc13783_connectivity"
# Anyone has readonly permission to IIM device file
KERNEL=="mxc_iim",  MODE="0444", SYMLINK+="mxc_mem"
KERNEL=="mxs_viim", MODE="0444", SYMLINK+="mxc_mem"
KERNEL=="mxc_ipu",  MODE="0666"
KERNEL=="mxc_vpu",  MODE="0666"
SUBSYSTEM=="video", MODE="0660"
KERNEL=="fb[0-9]",  MODE="0660", GROUP="video"
KERNEL=="gsl_kmod", MODE="0660", GROUP="video"
KERNEL=="galcore",  MODE="0660", GROUP="video"
```

# udev实战
UDEV实现U盘SD卡自动挂载/卸载并且拷贝数据

1.编译UDEV源码,执行arm-softfloat-linux-gnu-strip udev udevd udevstart udevinfo udevtest ,进行瘦身,并且拷贝这些文件到rootfs/bin文件夹下。

2.修改rootfs/etc/init.d/rcS 脚本，添加如下命令：

/bin/mount  -t  sysfs  sysfs /sys

/bin/mount  -t  tmpfs  tmpfs /dev

/bin/udevd  –-daemon              //创建udev的守护进程

/bin/udevstart                    //启动

3.在 /etc/udev/rules.d 目录下创建文件 10_usb.rules规则文件，他的语法是每个规则分成一个或多个“匹配”和“赋值”部分, 其内容如下

KERNEL=="sda1", SUBSYSTEM=="block", RUN+="/sbin/usbmount.sh"

KERNEL SUBSYSTEM 为匹配，RUN就是赋值，意为执行usbmount.sh这个脚本。

4.然后, 在 /sbin 目录中创建脚本文件usbmount.sh, 其内容为
```shell
#!/bin/sh
if [ “$ACTION” = “add” ]
    then
        mount -t vfat  /dev/sda1 /tmp/udisk
    mv   /mnt/yaffs/web_picture/*.jpg  /tmp/udisk
    mv   /mnt/yaffs/collect_picture/*.jpg  /tmp/udisk
elif [ “$ACTION” = "remove" ]
    then
        umount -l /tmp/udisk
fi
```
注：udisk、web_piture、collect_picture文件需自己建立
把该文件属性设置为可执行chmod 777 usbmount.sh
有一点需要注意的是指定的脚本解析器是sh，如果指定bash正常情况是无法解析这个脚本的，我们的嵌入式系统都没有bash。
插入U盘或者SD卡，触发add事件，执行10_usb.rules指定的/sbin/usbmount.sh脚本，因为是add ACTION，所以执行mount -t vfat  /dev/sda1 /tmp/udisk 。
拔出时，触发remove事件，执行10_usb.rules指定的/sbin/usbmount.sh脚本，因为是 ACTION 这时为remove，所以执行umount –l /tmp/udisk 。

# udevd源码分析
drivers/base/core.c：device_create()--->device_create_vargs()--->device_create_groups_vargs--->device_add()
--->kobject_uevent()--->kobject_uevent_env()
                            |
                            |
                            V
```c
/**
 * kobject_uevent_env - send an uevent with environmental data
 *
 * @action: action that is happening
 * @kobj: struct kobject that the action is happening to
 * @envp_ext: pointer to environmental data
 *
 * Returns 0 if kobject_uevent_env() is completed with success or the
 * corresponding error when it fails.
 */
int kobject_uevent_env(struct kobject *kobj, enum kobject_action action,
		       char *envp_ext[])
{
    // ... （省略其他注释）

    // search the kset we belong to
    // 寻找所属的 kset
    top_kobj = kobj;
    while (!top_kobj->kset && top_kobj->parent)
        top_kobj = top_kobj->parent;

    if (!top_kobj->kset) {
        pr_debug("kobject: '%s' (%p): %s: attempted to send uevent "
                 "without kset!\n", kobject_name(kobj), kobj,
                 __func__);
        return -EINVAL;
    }

    // ... （省略其他注释）

    // originating subsystem
    // 事件的来源子系统
    if (uevent_ops && uevent_ops->name)
        subsystem = uevent_ops->name(kset, kobj);
    else
        subsystem = kobject_name(&kset->kobj);
    if (!subsystem) {
        pr_debug("kobject: '%s' (%p): %s: unset subsystem caused the "
                 "event to drop!\n", kobject_name(kobj), kobj,
                 __func__);
        return 0;
    }

    // ... （省略其他注释）

    // environment buffer
    // 创建环境数据缓冲区
    env = kzalloc(sizeof(struct kobj_uevent_env), GFP_KERNEL);
    if (!env)
        return -ENOMEM;

    // ... （省略其他注释）

    // complete object path
    // 构建完整的对象路径
    devpath = kobject_get_path(kobj, GFP_KERNEL);
    if (!devpath) {
        retval = -ENOENT;
        goto exit;
    }

    // default keys
    // 添加默认键
    retval = add_uevent_var(env, "ACTION=%s", action_string);
    if (retval)
        goto exit;
    retval = add_uevent_var(env, "DEVPATH=%s", devpath);
    if (retval)
        goto exit;
    retval = add_uevent_var(env, "SUBSYSTEM=%s", subsystem);
    if (retval)
        goto exit;

    // keys passed in from the caller
    // 添加从调用者传入的键值对
    if (envp_ext) {
        for (i = 0; envp_ext[i]; i++) {
            retval = add_uevent_var(env, "%s", envp_ext[i]);
            if (retval)
                goto exit;
        }
    }

    // ... （省略其他注释）

    /* let the kset specific function add its stuff */
    // 调用 kset 特定函数添加额外的内容
    if (uevent_ops && uevent_ops->uevent) {
        // 如果 uevent_ops 存在且具有 uevent 函数
        retval = uevent_ops->uevent(kset, kobj, env);
        // 调用 kset 的 uevent 函数，并传递相应的参数
        if (retval) {
            // 如果 uevent 函数返回值不为零，表示出现了错误
            pr_debug("kobject: '%s' (%p): %s: uevent() returned "
                    "%d\n", kobject_name(kobj), kobj,
                    __func__, retval);
            goto exit;
        }
    }


exit:
    kfree(devpath);
    kfree(env);
    return retval;
}
EXPORT_SYMBOL_GPL(kobject_uevent_env);

```
udev工作过程如下：
（1）当内核检测到系统中出现新设备后，内核会通过netlink套接字发送uevent;
（2）udev获取内核发送的信息，进行规则匹配。从而创建设备节点。
udev是在设备模块加载时，通过扫描/sys/class/下的设备目录，继而在/dev/目录下生成设备文件节点的。

class_create/device_create/udev的基本工作流程：

（1） 驱动中使用class_create(…)函数，可以用它来创建一个类，这个类存放于sysfs下面（/sys/class）

（2）一旦创建好了这个类，再调用device_create(…)函数在/dev目录下创建相应的设备节点。

（3）insmod *.ko 加载模块的时候，用户空间中的udev会自动响应device_create(…)函数，去/sysfs下寻找对应的类从而创建设备节

# device_create能创建dev的设备又需要udevd干什么
 
`device_create` 函数是在 Linux 内核中用于创建设备节点的函数，通常在驱动程序中使用。这个函数创建的设备节点是内核空间的对象，用于向用户空间提供访问硬件设备的接口。`device_create` 并不依赖于 `udevd`，它在内核空间执行。

然而，用户空间的 `/dev` 目录中的设备文件通常是由 `udev` 守护进程创建和管理的。`udev` 负责在设备插拔事件发生时自动创建、删除和管理设备文件，使得用户和应用程序能够方便地访问硬件设备。`udev` 的作用在于：

1. **自动创建设备文件：** 当设备插入系统时，`udev` 可以自动为设备创建相应的设备文件，这样用户和应用程序可以通过这些设备文件来访问硬件设备，而无需手动创建设备文件。

2. **根据规则进行设备管理：** `udev` 使用预定义的规则来确定如何为特定设备创建设备文件，以及如何设置权限、属性等。这使得设备管理变得灵活，可以根据设备属性和类型进行不同的处理。

3. **设备节点持久化：** `udev` 确保设备文件的名称是持久的，并不会因为设备插拔而变化。这有助于应用程序在设备插拔后继续正常工作。

因此，虽然 `device_create` 可以在内核中创建设备节点，但是 `udev` 在用户空间中负责创建和管理 `/dev` 目录下的设备文件，使设备访问更加方便、自动化和持久化。两者在不同的层级发挥作用，`device_create` 在内核空间创建设备节点，而 `udev` 在用户空间创建和管理设备文件。