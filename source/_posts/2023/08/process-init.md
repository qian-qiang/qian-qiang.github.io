---
title: process-init
top: false
cover: false
toc: true
mathjax: true
date: 2023-08-24 14:37:55
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

# init进程
在Linux系统中，`init` 是第一个被启动的进程，其进程ID为1。它是系统启动过程中的第一个用户级进程，负责初始化系统，并在系统运行时作为所有其他进程的祖先。然而，需要注意的是，在现代Linux系统中，`init` 进程通常被替代为更先进的初始化系统，比如 `systemd` 或 `Upstart`。

原始的 `init` 进程主要负责以下几个任务：

1. **系统初始化**: `init` 进程在系统启动时负责加载操作系统所需的核心模块和设备驱动程序，以确保系统的基本功能正常运行。

2. **启动和管理系统服务**: `init` 进程通过运行启动脚本来启动系统中的各种服务和守护进程。这些服务可能包括网络服务、文件系统服务、打印服务等。

3. **运行级别管理**: `init` 进程支持不同的运行级别，每个级别定义了不同的系统状态。例如，运行级别可能是单用户模式、多用户模式、图形用户界面模式等。`init` 进程负责根据需要切换不同的运行级别。

然而，随着时间的推移，传统的 `init` 进程的功能显得有些有限，因此引入了更现代的初始化系统，如 `systemd`。`systemd` 在许多Linux发行版中取代了传统的 `init`，它提供了更强大的系统初始化和管理功能，可以更有效地处理并行启动、服务依赖、日志管理等。

尽管如此，`init` 进程作为系统的第一个进程仍然具有重要的历史地位，并且在某些方面仍然发挥着作用，尤其是在一些较旧的或嵌入式系统中。

# init源码
init/main.c：start_kernel()--->rest_init()
```c
static noinline void __init_refok rest_init(void)
{
    int pid;

    // 启动RCU（Read-Copy-Update）调度器
    rcu_scheduler_starting();

    // 初始化SMP（Symmetric Multiprocessing）启动线程
    smpboot_thread_init();

    /*
     * 我们需要首先生成 init 进程，以便它获得 pid 1，但是 init 任务最终会想要创建 kthread，
     * 如果我们在创建 kthreadd 之前调度它，将会导致 OOPS（操作系统崩溃）。
     */
    kernel_thread(kernel_init, NULL, CLONE_FS);

    // 设置 NUMA（Non-Uniform Memory Access）默认策略
    numa_default_policy();

    // 创建 kthreadd 进程，用于创建其他内核线程
    pid = kernel_thread(kthreadd, NULL, CLONE_FS | CLONE_FILES);

    // 读取锁定 RCU，以查找 kthreadd 进程的任务结构体
    rcu_read_lock();
    kthreadd_task = find_task_by_pid_ns(pid, &init_pid_ns);
    rcu_read_unlock();

    // 标记 kthreadd 进程已完成初始化
    complete(&kthreadd_done);

    /*
     * 引导空闲线程必须执行 schedule() 至少一次以启动系统：
     */
    init_idle_bootup_task(current);
    schedule_preempt_disabled();
    
    /* 带有抢占禁用的情况下调用 cpu_idle */
    cpu_startup_entry(CPUHP_ONLINE);
}
```
这段代码主要完成以下任务：

1.启动 RCU 调度器，这是一种内核中用于实现无锁并发访问的机制。
2.初始化 SMP 启动线程，用于初始化多处理器系统。
3.创建 init 进程，确保它获得 PID 1，但避免在创建 kthreadd 进程之前调度 init 进程。
4.设置 NUMA 默认策略，处理非一致性内存访问。
5.创建 kthreadd 进程，该进程用于在内核中创建其他线程。
6.根据 PID 查找并初始化 kthreadd 进程的任务结构体。
7.标记 kthreadd 进程初始化完成。
8.启动引导空闲线程，执行初始的调度以启动系统。
9.最后，调用 cpu_startup_entry，在线程上下文中启动 CPU，允许它执行调度。

```c
    static int __ref kernel_init(void *unused)
    {
        int ret;

        // 运行 kernel_init_freeable 函数，执行一些必要的内核初始化
        kernel_init_freeable();

        // 在释放内存之前，需要完成所有异步 __init 代码
        async_synchronize_full();

        // 释放初始内存
        free_initmem();

        // 将只读数据段标记为只读
        mark_rodata_ro();

        // 设置系统状态为 SYSTEM_RUNNING，表示系统已运行
        system_state = SYSTEM_RUNNING;

        // 设置 NUMA 默认策略
        numa_default_policy();

        // 清理延迟的文件指针释放
        flush_delayed_fput();

        // 如果设置了 ramdisk_execute_command，则尝试运行对应的命令
        if (ramdisk_execute_command) {
            ret = run_init_process(ramdisk_execute_command);
            if (!ret)
                return 0;
            pr_err("Failed to execute %s (error %d)\n",
                ramdisk_execute_command, ret);
        }

        /*
        * 我们尝试执行以下每个命令，直到成功为止。
        *
        * 如果我们尝试恢复一个非常破损的机器，可以使用 Bourne shell 代替 init。
        */
        if (execute_command) {
            ret = run_init_process(execute_command);
            if (!ret)
                return 0;
            panic("Requested init %s failed (error %d).",
                execute_command, ret);
        }
        if (!try_to_run_init_process("/sbin/init") ||
            !try_to_run_init_process("/etc/init") ||
            !try_to_run_init_process("/bin/init") ||
            !try_to_run_init_process("/bin/sh"))
            return 0;

        // 如果没有找到可用的 init 进程，触发内核崩溃
        panic("No working init found.  Try passing init= option to kernel. "
            "See Linux Documentation/init.txt for guidance.");
    }
```
这段代码的主要功能是在系统引导期间执行一系列初始化操作，然后尝试启动系统的初始化进程（如 init）。它的核心步骤包括：

运行 kernel_init_freeable 函数，执行一些必要的内核初始化,这个函数很重要后面分析。

在释放内存之前，使用 async_synchronize_full 等待所有异步初始化代码的完成。

释放初始内存，这是在引导过程中使用的一部分内存。

将只读数据段标记为只读，以提高系统的安全性。

设置系统状态为 SYSTEM_RUNNING，表示系统已经正常运行。

设置 NUMA 默认策略，用于处理非一致性内存访问。

清理延迟的文件指针释放，确保文件资源得到正确管理。

尝试执行预设的 ramdisk_execute_command 命令（如果设置了）。

尝试执行预设的 execute_command 命令（如果设置了）。

如果以上尝试都失败，尝试依次执行一些默认的初始化命令路径，如 /sbin/init、/etc/init、/bin/init 和 /bin/sh。
`/sbin/init实际是init.sysvinit。但是init.sysvinit是干嘛的不知道？？？？`
暂时理解成init进程启动，通过/sbin/init准备系统软件的运行环境，读取/etc/inittab，获取运行级别数值 

如果仍然找不到可用的初始化进程，系统进入崩溃状态，显示错误消息并建议尝试通过内核参数 init= 指定初始化进程。

```c

static noinline void __init kernel_init_freeable(void)
{
	/*
	 * Wait until kthreadd is all set-up.
	 */
	wait_for_completion(&kthreadd_done);

	/* Now the scheduler is fully set up and can do blocking allocations */
	gfp_allowed_mask = __GFP_BITS_MASK;

	/*
	 * init can allocate pages on any node
	 */
	set_mems_allowed(node_states[N_MEMORY]);
	/*
	 * init can run on any cpu.
	 */
	set_cpus_allowed_ptr(current, cpu_all_mask);

	cad_pid = task_pid(current);

	smp_prepare_cpus(setup_max_cpus);

	do_pre_smp_initcalls();
	lockup_detector_init();

	smp_init();
	sched_init_smp();

	do_basic_setup();   /* 设备初始化都在此函数中完成 */

	/* Open the /dev/console on the rootfs, this should never fail */
	if (sys_open((const char __user *) "/dev/console", O_RDWR, 0) < 0)
		pr_err("Warning: unable to open an initial console.\n");

	(void) sys_dup(0);
	(void) sys_dup(0);
	/*
	 * check if there is an early userspace init.  If yes, let it do all
	 * the work
	 */

	if (!ramdisk_execute_command)
		ramdisk_execute_command = "/init";

	if (sys_access((const char __user *) ramdisk_execute_command, 0) != 0) {
		ramdisk_execute_command = NULL;
		prepare_namespace();
	}

	/*
	 * Ok, we have completed the initial bootup, and
	 * we're essentially up and running. Get rid of the
	 * initmem segments and start the user-mode stuff..
	 *
	 * rootfs is available now, try loading the public keys
	 * and default modules
	 */

	integrity_load_keys();
	load_default_modules();
}
```
`kernel_init_freeable`函数执行的一系列操作：

1. `wait_for_completion(&kthreadd_done);`：等待直到`kthreadd`进程初始化完成，确保`kthreadd`进程已经准备就绪。

2. `gfp_allowed_mask = __GFP_BITS_MASK;`：设置内核的内存分配标志，允许使用所有内存分配标志位。

3. `set_mems_allowed(node_states[N_MEMORY]);`：设置进程可以在所有NUMA节点上分配内存。

4. `set_cpus_allowed_ptr(current, cpu_all_mask);`：设置当前进程可以在所有CPU上运行。

5. `cad_pid = task_pid(current);`：设置`cad_pid`（Ctrl+Alt+Del进程）为当前进程的PID。

6. `smp_prepare_cpus(setup_max_cpus);`：准备启动SMP（对称多处理）系统，设置CPU的最大数量。

7. `do_pre_smp_initcalls();`：运行预初始化的SMP调用。

8. `lockup_detector_init();`：初始化系统的死锁检测器。

9. `smp_init();`：初始化SMP子系统。

10. `sched_init_smp();`：初始化调度器的SMP相关部分。

11. `do_basic_setup();`：do_basic_setup 函数用于完成 Linux 下设备驱动初始化工作！非常重要。do_basic_setup 会调用 driver_init 函数完成 Linux 下驱动模型子系统的初始化。

12. `sys_open((const char __user *) "/dev/console", O_RDWR, 0)`：尝试打开`/dev/console`设备，用于系统控制台输出。

13. `sys_dup(0)`：通过复制文件描述符0（标准输入）来创建文件描述符1和2（标准输出和标准错误），确保它们都指向同一个设备。

14. `if (!ramdisk_execute_command) ramdisk_execute_command = "/init";`：如果没有定义`ramdisk_execute_command`，则设置默认的启动命令为`/init`。

15. `if (sys_access((const char __user *) ramdisk_execute_command, 0) != 0)`：检查指定的启动命令是否存在。

16. `prepare_namespace();`：准备初始化的根文件系统命名空间。

17. `integrity_load_keys();`：加载完整性校验的公钥，用于验证文件系统上的数据完整性。

18. `load_default_modules();`：加载默认的内核模块，增加系统功能。

总之，这段代码在系统引导期间完成一系列重要的初始化步骤，包括设置内存分配、CPU调度、设备初始化、根文件系统设置等。最终，它准备好系统的运行环境，使得系统能够顺利进入用户模式运行，并提供用户可见的功能。

# 执行脚本
    sbin/init--->init.sysinit
                    |调用
                    v
        /etc/inittab--->/etc/init.d/rcS--->/etc/default/rcS（默认设置）
                                       --->/etc/init.d/rc（启动默认线程）
                                            |
                                            V
                                        开启/etc/rc$.d/下面的进程
## /etc/inittab
```c
root@ATK-IMX6U:/etc# cat inittab 
# /etc/inittab: init(8) configuration.
# $Id: inittab,v 1.91 2002/01/25 13:35:21 miquels Exp $

# The default runlevel.
id:5:initdefault:

# Boot-time system configuration/initialization script.
# This is run first except when booting in emergency (-b) mode.
si::sysinit:/etc/init.d/rcS

# What to do in single-user mode.
~~:S:wait:/sbin/sulogin

# /etc/init.d executes the S and K scripts upon change
# of runlevel.
#
# Runlevel 0 is halt.
# Runlevel 1 is single-user.
# Runlevels 2-5 are multi-user.
# Runlevel 6 is reboot.
tty1::askfirst:-/bin/sh
l0:0:wait:/etc/init.d/rc 0
l1:1:wait:/etc/init.d/rc 1
l2:2:wait:/etc/init.d/rc 2
l3:3:wait:/etc/init.d/rc 3
l4:4:wait:/etc/init.d/rc 4
l5:5:wait:/etc/init.d/rc 5
l6:6:wait:/etc/init.d/rc 6
# Normally not reached, but fallthrough in case of emergency.
z6:6:respawn:/sbin/sulogin
#mxc0:12345:respawn:/bin/start_getty 115200 ttymxc0
mxc0:12345:respawn:/sbin/getty -l /bin/autologin -n -L 115200 ttymxc0
# /sbin/getty invocations for the runlevels.
#
# The "id" field MUST be the same as the last
# characters of the device (after "tty").
#
# Format:
#  <id>:<runlevels>:<action>:<process>
#

1:12345:respawn:/sbin/getty 38400 tty1

```
这是一个典型的 `/etc/inittab` 文件，该文件在旧版本的 Linux 系统中用于配置系统初始化过程和运行级别。该文件告诉初始化系统（通常是 SysVinit）在不同运行级别下要执行的操作。以下是`inittab` 文件的内容解释：

1. `id:5:initdefault:`：这指定默认的运行级别为 5，通常对应多用户图形界面模式（X11）。

2. `si::sysinit:/etc/init.d/rcS`：在系统引导过程中运行 `/etc/init.d/rcS` 脚本，这是系统初始化脚本，执行一些基本的系统配置。

3. `~~:S:wait:/sbin/sulogin`：在单用户模式下，等待并运行 `/sbin/sulogin`，该命令是用于单用户模式下的登录。

4. 运行级别定义及操作：
   - `l0:0:wait:/etc/init.d/rc 0` 切换到运行级别 0（关机）时，运行 `/etc/init.d/rc 0` 脚本。
   - `l1:1:wait:/etc/init.d/rc 1` 切换到运行级别 1（单用户模式）时，运行 `/etc/init.d/rc 1` 脚本。
   - `l2:2:wait:/etc/init.d/rc 2` 切换到运行级别 2 时，运行 `/etc/init.d/rc 2` 脚本。
   - `l3:3:wait:/etc/init.d/rc 3` 切换到运行级别 3 时，运行 `/etc/init.d/rc 3` 脚本。
   - `l4:4:wait:/etc/init.d/rc 4` 切换到运行级别 4 时，运行 `/etc/init.d/rc 4` 脚本。
   - `l5:5:wait:/etc/init.d/rc 5` 切换到运行级别 5 时，运行 `/etc/init.d/rc 5` 脚本。
   - `l6:6:wait:/etc/init.d/rc 6` 切换到运行级别 6（重启）时，运行 `/etc/init.d/rc 6` 脚本。

5. `z6:6:respawn:/sbin/sulogin`：在运行级别 6（重启）时，启动 `/sbin/sulogin`。

6. `mxc0:12345:respawn:/sbin/getty -l /bin/autologin -n -L 115200 ttymxc0`：在运行级别 1、2、3、4、5 时，通过 `getty` 在串口设备 `ttymxc0` 上启动自动登录的终端会话。

7. `1:12345:respawn:/sbin/getty 38400 tty1`：在运行级别 1、2、3、4、5 时，通过 `getty` 在终端 `tty1` 上启动交互式终端会话。

`/etc/inittab` 文件是一个配置文件，用于定义系统初始化进程的行为和运行级别。在早期的 UNIX 和类 UNIX 系统中，`init` 进程是系统中的第一个进程，它是所有其他进程的祖先。`/etc/inittab` 文件用于指定在系统引导过程中要执行的任务、默认运行级别以及其他与系统初始化和运行级别相关的设置。

主要功能包括：

1. **定义运行级别（Runlevels）：** `/etc/inittab` 文件允许您指定默认的运行级别，例如单用户模式、多用户模式等。每个运行级别对应于一组要在该级别下启动或停止的服务。

2. **定义启动任务：** 您可以在 `/etc/inittab` 中定义在不同运行级别下要执行的任务和脚本。这些任务可以是初始化系统配置、启动服务、创建虚拟终端等。例如，在启动时自动运行网络配置脚本。

3. **设置控制台：** `/etc/inittab` 可以配置系统的虚拟终端（TTY）。您可以定义哪个虚拟终端用于登录，哪个终端用于系统控制台，以及何时启动 getty 进程等。

4. **设置自动登录：** 您可以配置系统以在特定终端上自动登录用户，这在某些场景下很有用，例如嵌入式系统中的自动化测试。

5. **定义执行任务：** 您可以将执行任务与特定运行级别相关联。这些任务可能是脚本、命令或程序，会在切换到相关运行级别时自动执行。

需要注意的是，现代 Linux 系统中，许多发行版已经迁移到了更现代的初始化系统，如 `systemd`。因此，`/etc/inittab` 在某些发行版中可能不再被广泛使用。不过，它在一些特定的环境中仍然可以用来定义一些系统初始化和运行级别相关的配置。

## /etc/init.d/rcS
```C
#!/bin/sh
#
# rcS           Call all S??* scripts in /etc/rcS.d in
#               numerical/alphabetical order.
#
# Version:      @(#)/etc/init.d/rcS  2.76  19-Apr-1999  miquels@cistron.nl
#

PATH=/sbin:/bin:/usr/sbin:/usr/bin
runlevel=S
prevlevel=N
umask 022
export PATH runlevel prevlevel

#       Make sure proc is mounted
#
[ -d "/proc/1" ] || mount /proc

#
#       Source defaults.
#
. /etc/default/rcS

#
#       Trap CTRL-C &c only in this shell so we can interrupt subprocesses.
#
trap ":" INT QUIT TSTP

#
#       Call all parts in order.
#
exec /etc/init.d/rc S
```
这是 `/etc/init.d/rcS` 脚本的内容，用于在引导过程中执行一些初始化操作：

1. `PATH=/sbin:/bin:/usr/sbin:/usr/bin`：设置执行脚本时的环境变量路径，以确保能够找到所需的命令和工具。

2. `runlevel=S`：设置当前运行级别为 S（系统启动）。

3. `prevlevel=N`：设置上一个运行级别为 N（不存在的运行级别）。

4. `umask 022`：设置文件创建的默认权限掩码，确保创建的文件不会过于开放。

5. `export PATH runlevel prevlevel`：导出 `PATH`、`runlevel` 和 `prevlevel` 变量，以便在子进程中使用。

6. `[ -d "/proc/1" ] || mount /proc`：检查 `/proc/1` 目录是否存在，如果不存在则挂载 `/proc` 文件系统，确保系统可以访问进程信息。

7. `. /etc/default/rcS`：通过 sourcing（`.`）导入 `/etc/default/rcS` 文件，用于加载一些默认配置。

8. `trap ":" INT QUIT TSTP`：设置信号处理，将 `INT`、`QUIT` 和 `TSTP` 信号的处理设为什么都不做（`:` 表示空语句），以便可以中断子进程而不中断脚本自身。

9. `exec /etc/init.d/rc S`：通过 `exec` 命令执行 `/etc/init.d/rc` 脚本，并传递参数 `S`，表示在运行级别 S 下执行脚本。

`/etc/init.d/rcS` 文件是一个脚本文件，用于在系统引导过程中执行一系列初始化任务。这些任务通常是与系统硬件、网络、文件系统挂载等相关的操作，以确保系统在启动时能够正常运行。

在许多 Linux 发行版中，`rcS` 脚本被称为"System Initialization Script"，它是启动过程中第一个执行的脚本。`rcS` 脚本的主要目的是准备系统环境，使其达到可用状态，然后将控制权交给其他初始化脚本，以继续完成系统启动。

`/etc/init.d/rcS` 脚本的功能可能包括：

1. **挂载文件系统：** `rcS` 可能会在此阶段挂载根文件系统和其他必需的文件系统，以确保系统可以访问所需的文件和配置信息。

2. **设置网络：** 在启动过程中，`rcS` 可能会配置网络接口，启动网络服务并初始化网络设置，以便系统可以与其他计算机进行通信。

3. **加载模块：** 一些硬件或功能可能需要内核模块支持。`rcS` 可能会加载所需的内核模块，以确保硬件能够正常运作。

4. **启动服务：** `rcS` 可能会启动一些基本的系统服务，例如系统日志记录、时间同步等。

5. **设置系统参数：** `rcS` 可能会设置系统参数、环境变量和其他系统配置，以确保系统在正常运行时能够获得正确的设置。

6. **清理临时文件：** 在引导过程中，系统可能会生成临时文件。`rcS` 可能会在启动后清理这些临时文件，以保持系统的整洁性。

7. **执行其他初始化任务：** 根据发行版和系统配置，`rcS` 可能会执行其他必要的初始化任务，以确保系统正确启动。

需要注意的是，`/etc/init.d/rcS` 在不同的 Linux 发行版中可能会有不同的实现和用途。在一些现代发行版中，可能已经过渡到使用更现代的初始化系统，如 `systemd`，而一些传统的发行版可能仍然使用 `rcS` 脚本作为系统初始化的一部分。

## /etc/default/rcS
```c
#
#       /etc/rcS.d 中启动脚本的默认值
#

# 在 /tmp 中保留时间文件的天数。
TMPTIME=0
# 如果要在引导时启动 sulogin，请设置为 yes
SULOGIN=no
# 如果希望在系统启动完成之前（即 inetd 启动后）能够通过 telnet/rlogin 登录，请设置为 no
DELAYLOGIN=no
# 假定 BIOS 时钟设置为 UTC 时间（推荐）
UTC=yes
# 如果希望引导时更加安静，请将 VERBOSE 设置为 "no"
VERBOSE=no
# 如果不希望自动编辑 /etc/motd，请将 EDITMOTD 设置为 "no"
EDITMOTD=no
# 是否在引导时对根文件系统执行 fsck（文件系统检查）
ENABLE_ROOTFS_FSCK=no
# 如果希望在启动时将 "-y" 添加到 fsck 命令，请将 FSCKFIX 设置为 "yes"
FSCKFIX=yes
# 将 TICKADJ 设置为适用于此特定机器的正确 tick 值
#TICKADJ=10000
# 在 populate-volatile.sh 中启用缓存
VOLATILE_ENABLE_CACHE=yes
# 指示根文件系统是否打算为只读。设置 ROOTFS_READ_ONLY 为 yes 并重新启动将使根文件系统变为只读。
# 通常情况下，您不应更改此值。
ROOTFS_READ_ONLY=no

```
/etc/default/rcS 文件是一个配置文件，用于设置系统初始化过程中的默认参数和选项。该文件中的设置会影响系统引导和初始化的行为。在许多 Linux 发行版中，/etc/default/rcS 文件用于指定与系统启动过程有关的全局设置。

## /etc/init.d/rc
```shell
#!/bin/sh
#
# rc            当运行级别变化时，此文件负责启动/停止服务。
#
# 优化特性：
# 在服务在前一个运行级别中正在运行且在运行级别转换中没有被停止时，_不会_运行启动脚本
# （大多数 Debian 服务在 rc{1,2,3,4,5} 中没有 K?? 链接）
#
# 作者：Miquel van Smoorenburg <miquels@cistron.nl>
#      Bruce Perens <Bruce@Pixar.com>
#
# 版本：@(#)rc  2.78  1999 年 11 月 7 日  miquels@cistron.nl
#

. /etc/default/rcS
export VERBOSE

startup_progress() {
    step=$(($step + $step_change))
    if [ "$num_steps" != "0" ]; then
        progress=$((($step * $progress_size / $num_steps) + $first_step))
    else
        progress=$progress_size
    fi
    #echo "PROGRESS is $progress $runlevel $first_step + ($step of $num_steps) $step_change $progress_size"
    if type psplash-write >/dev/null 2>&1; then
        TMPDIR=/mnt/.psplash psplash-write "PROGRESS $progress" || true
    fi
    #if [ -e /mnt/.psplash/psplash_fifo ]; then
    #    echo "PROGRESS $progress" > /mnt/.psplash/psplash_fifo
    #fi
}

startup() {
  # 处理冗长性
  [ "$VERBOSE" = very ] && echo "INIT: 正在运行 $@..."

  case "$1" in
        *.sh)
                # 为了提高速度，源码中的 shell 脚本。
                (
                        trap - INT QUIT TSTP
                        scriptname=$1
                        shift
                        . $scriptname
                )
                ;;
        *)
                "$@"
                ;;
  esac
  startup_progress
}

# 仅在此 shell 中忽略 CTRL-C，以便可以中断子进程。
trap ":" INT QUIT TSTP

# 设置 onlcr 以避免楼梯效应。
stty onlcr 0>&1

# 限制启动脚本的栈大小
[ "$STACK_SIZE" == "" ] || ulimit -S -s $STACK_SIZE

# 现在找出当前运行级别和上一个运行级别是什么。

runlevel=$RUNLEVEL
# 获取第一个参数。将新运行级别设置为此参数。
[ "$1" != "" ] && runlevel=$1
if [ "$runlevel" = "" ]
then
        echo "用法：$0 <运行级别>" >&2
        exit 1
fi
previous=$PREVLEVEL
[ "$previous" = "" ] && previous=N

export runlevel previous

# 是否有适用于这个新运行级别的 rc 目录？
if [ -d /etc/rc$runlevel.d ]
then
        # 找出 initramfs 在进度条中的位置。
        PROGRESS_STATE=0
        #if [ -f /dev/.initramfs/progress_state ]; then
        #    . /dev/.initramfs/progress_state
        #fi

        # 将进度条的剩余部分分为三份
        progress_size=$(((100 - $PROGRESS_STATE) / 3))

        case "$runlevel" in
                0|6)
                        # 从 -100 倒计时到 0，使用整个进度条
                        first_step=-100
                        progress_size=100
                        step_change=1
                        ;;
                S)
                        # 从 initramfs 剩余的位置开始，使用剩余空间的 2/3
                        first_step=$PROGRESS_STATE
                        progress_size=$(($progress_size * 2))
                        step_change=1
                        ;;
                *)
                        # 从 rcS 停止的位置开始，使用最后 1/3 的空间（通过保持 progress_size 不变）
                        first_step=$(($progress_size * 2 + $PROGRESS_STATE))
                        step_change=1
                        ;;
        esac

        num_steps=0
        for s in /etc/rc$runlevel.d/[SK]*; do
            case "${s##/etc/rc$runlevel.d/S??}" in
                gdm|xdm|kdm|reboot|halt)
                    break
                    ;;
            esac
            num_steps=$(($num_steps + 1))
        done
        step=0

        # 首先，运行 KILL 脚本。
        if [ $previous != N ]
        then
                for i in /etc/rc$runlevel.d/K[0-9][0-9]*
                do
                        # 检查脚本是否存在。
                        [ ! -f $i ] && continue

                        # 停止服务。
                        startup $i stop
                done
        fi

        # 现在运行此运行级别的 START 脚本。
        for i in /etc/rc$runlevel.d/S*
        do
                [ ! -f $i ] && continue

                if [ $previous != N ] && [ $previous != S ]
                then
                        #
                        # 在前一个运行级别中找到启动脚本和
                        # 在这个运行级别中找到停止脚本。
                        #
                        suffix=${i#/etc/rc$runlevel.d/S[0-9][0-9]}
                        stop=/etc/rc$runlevel.d/K[0-9][0-9]$suffix
                        previous_start=/etc/rc$previous.d/S[0-9][0-9]$suffix
                        #
                        # 如果在上一个级别中有启动脚本
                        # 并且在这个级别中没有停止脚本，我们就不需要重新启动服务。
                        #
                        [ -f $previous_start ] && [ ! -f $stop ] && continue
                fi
                case "$runlevel" in
                        0|6)
                                startup $i stop
                                ;;
                        *)
                                startup $i start
                                ;;
                esac
        done
  fi

# 取消注释以在手动退出 psplash，否则在看到 VC 切换时会退出
if [ "x$runlevel" != "xS" ] && [ ! -x /etc/rc${runlevel}.d/S??xserver-nodm ]; then
    if type psplash-write >/dev/null 2>&1; then
        TMPDIR=/mnt/.psplash psplash-write "QUIT" || true
        umount -l /mnt/.psplash
    fi
fi

```
由/etc/init.d/rc在执行等级切换的时候在/etc/rc$runlevel.d文件夹中启动相关程序，例如切换到runevel 5
```c
root@ATK-IMX6U:/etc/rc5.d# ls -l
total 0
lrwxrwxrwx 1 root root 20 Jun 10 18:21 S01networking -> ../init.d/networking
lrwxrwxrwx 1 root root 22 Jun 10 18:21 S01xserver-nodm -> ../init.d/xserver-nodm
lrwxrwxrwx 1 root root 16 Jun 10 18:21 S02dbus-1 -> ../init.d/dbus-1
lrwxrwxrwx 1 root root 17 Jun 10 18:21 S05connman -> ../init.d/connman
lrwxrwxrwx 1 root root 18 Jun 10 18:21 S10dropbear -> ../init.d/dropbear
lrwxrwxrwx 1 root root 17 Jun 10 18:21 S12rpcbind -> ../init.d/rpcbind
lrwxrwxrwx 1 root root 21 Jun 10 18:21 S15mountnfs.sh -> ../init.d/mountnfs.sh
lrwxrwxrwx 1 root root 21 Jun 10 18:21 S15watchdog.sh -> ../init.d/watchdog.sh
lrwxrwxrwx 1 root root 19 Jun 10 18:21 S19nfscommon -> ../init.d/nfscommon
lrwxrwxrwx 1 root root 14 Jun 10 18:21 S20apmd -> ../init.d/apmd
lrwxrwxrwx 1 root root 13 Jun 10 18:21 S20atd -> ../init.d/atd
lrwxrwxrwx 1 root root 17 Jun 10 18:21 S20hostapd -> ../init.d/hostapd
lrwxrwxrwx 1 root root 20 Jun 10 18:21 S20hwclock.sh -> ../init.d/hwclock.sh
lrwxrwxrwx 1 root root 19 Jun 10 18:21 S20nfsserver -> ../init.d/nfsserver
lrwxrwxrwx 1 root root 16 Jun 10 18:21 S20syslog -> ../init.d/syslog
lrwxrwxrwx 1 root root 22 Jun 10 18:21 S21avahi-daemon -> ../init.d/avahi-daemon
lrwxrwxrwx 1 root root 15 Jun 10 18:21 S22ofono -> ../init.d/ofono
lrwxrwxrwx 1 root root 15 Jun 10 18:21 S64neard -> ../init.d/neard
lrwxrwxrwx 1 root root 16 Jun 10 18:21 S80vsftpd -> ../init.d/vsftpd
lrwxrwxrwx 1 root root 15 Jun 10 18:21 S90crond -> ../init.d/crond
lrwxrwxrwx 1 root root 15 Jun 10 18:21 S92nginx -> ../init.d/nginx
lrwxrwxrwx 1 root root 18 Jun 10 18:21 S99rc.local -> ../init.d/rc.local
lrwxrwxrwx 1 root root 22 Jun 10 18:21 S99rmnologin.sh -> ../init.d/rmnologin.sh
lrwxrwxrwx 1 root root 23 Jun 10 18:21 S99stop-bootlogd -> ../init.d/stop-bootlogd
root@ATK-IMX6U:/etc/rc5.d# # diff  rc3.d/ rc5.d/
Only in rc3.d/: K01xserver-nodm
Only in rc5.d/: S01xserver-nodm
diff: rc3.d/S20hostapd: No such file or directory
diff: rc5.d/S20hostapd: No such file or directory

```
`/etc/init.d/rc` 文件是一个启动脚本，用于在系统的不同运行级别（runlevel）之间切换时启动或停止服务。在许多 Linux 系统中，运行级别是系统运行状态的一个标识，不同的运行级别对应于不同的系统配置和功能。

在传统的 SysV init 系统中，`/etc/init.d/rc` 脚本是一个管理系统运行级别的关键脚本。它接受一个参数，即目标运行级别，然后根据当前运行级别和目标运行级别执行必要的操作以启动或停止服务。这通常涉及启动或停止各种服务脚本（以脚本符号 S 或 K 开头的脚本），以实现系统的初始化或关机。

具体而言，`/etc/init.d/rc` 脚本的主要功能包括：

1. **判断运行级别：** 根据脚本参数和当前运行级别，确定要切换到的目标运行级别。

2. **执行运行级别切换操作：** 根据目标运行级别，执行一系列操作以启动或停止与该运行级别相关的服务。

3. **启动服务：** 如果切换到一个新的运行级别，`rc` 脚本会依次启动以 `S` 开头的服务脚本。这些服务脚本负责启动系统所需的各种服务，如网络、文件系统挂载、系统日志等。

4. **停止服务：** 如果切换到一个较低的运行级别，`rc` 脚本会依次停止以 `K` 开头的服务脚本。这些服务脚本负责停止系统中正在运行的服务。

5. **设置环境：** `rc` 脚本可能会设置环境变量或其他参数，以便在运行服务脚本时传递所需的信息。

需要注意的是，随着现代 Linux 发行版的发展，许多系统已经转向使用 `systemd` 或其他更现代的初始化系统，而不再使用传统的 SysV init 系统。因此，`/etc/init.d/rc` 在一些新的发行版中可能已经不再起到关键的作用，而是由更现代的初始化系统负责管理运行级别和服务启动。

如果你使用的是基于 SysV init 的系统，并且遇到了与 `/etc/init.d/rc` 相关的问题，你可能需要深入了解你的系统文档和初始化流程，以理解脚本是如何工作的以及如何进行定制。