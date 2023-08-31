---
title: process-kthreadd
top: false
cover: false
toc: true
mathjax: true
date: 2023-08-25 08:51:44
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

# kthread进程
`kthread` 是 Linux 内核中的一种线程类型，它用于执行内核空间的工作。这些线程通常用于处理一些需要在内核中运行的任务，而不会阻塞整个系统。以下是一些 `kthread` 线程的主要用途：

1. **后台工作：** `kthread` 线程通常用于执行与系统管理和维护相关的后台任务。例如，定期执行清理操作、处理未完成的任务、回收资源等。

2. **异步处理：** 内核中的一些操作可能需要在后台执行，而不阻塞主要执行路径。使用 `kthread` 可以在后台进行这些操作，以确保主要执行路径的响应性。

3. **延迟操作：** 某些操作可能需要在某些条件满足后才能执行，例如在资源可用时才进行操作。`kthread` 可以用于定期检查这些条件，并在满足时执行操作。

4. **并发处理：** 内核可能需要同时执行多个任务，例如处理多个网络连接或设备请求。使用 `kthread` 可以实现这种并发处理。

5. **设备驱动程序：** 设备驱动程序可能需要在后台执行某些操作，如处理中断、清理资源、维护设备状态等。

6. **事件通知：** `kthread` 线程可以用于监听特定事件，一旦事件发生，线程可以处理相应的操作。

总之，`kthread` 线程在内核中为开发者提供了一种执行后台任务、异步操作、并发处理等操作的方式，同时不会阻塞整个系统。这对于确保系统的响应性、资源管理和后台任务的执行非常有用。

# kthread源码
```c

static noinline void __init_refok rest_init(void)
{
	int pid;

	rcu_scheduler_starting();
	smpboot_thread_init();
	/*
	 * We need to spawn init first so that it obtains pid 1, however
	 * the init task will end up wanting to create kthreads, which, if
	 * we schedule it before we create kthreadd, will OOPS.
	 */
	kernel_thread(kernel_init, NULL, CLONE_FS);
	numa_default_policy();
	pid = kernel_thread(kthreadd, NULL, CLONE_FS | CLONE_FILES);
	rcu_read_lock();
	kthreadd_task = find_task_by_pid_ns(pid, &init_pid_ns);
	rcu_read_unlock();
	complete(&kthreadd_done);

	/*
	 * The boot idle thread must execute schedule()
	 * at least once to get things moving:
	 */
	init_idle_bootup_task(current);
	schedule_preempt_disabled();
	/* Call into cpu_idle with preempt disabled */
	cpu_startup_entry(CPUHP_ONLINE);
}
```

```c
/**
 * kthreadd - 内核线程创建和管理函数
 * @unused: 未使用的指针（内核线程函数签名所需）
 *
 * 此函数作为内核线程创建和管理的入口点。
 * 它负责为子线程设置干净的上下文以继承，管理其调度，并根据需要创建新的内核线程。
 */
int kthreadd(void *unused)
{
    struct task_struct *tsk = current;

    /* 为子线程设置一个干净的上下文。 */
    set_task_comm(tsk, "kthreadd");  // 设置线程的名称为 "kthreadd"
    ignore_signals(tsk);  // 忽略信号，确保线程不受外部信号的干扰
    set_cpus_allowed_ptr(tsk, cpu_all_mask);  // 允许线程在所有 CPU 上运行
    set_mems_allowed(node_states[N_MEMORY]);  // 允许线程在特定内存节点上运行

    current->flags |= PF_NOFREEZE;  // 设置标志，防止线程被冻结（挂起）

    for (;;) {  // 无限循环，管理线程的创建和调度
        set_current_state(TASK_INTERRUPTIBLE);  // 将线程状态设置为可中断睡眠状态
        
        /* 如果 kthread 创建请求列表为空，则等待事件。 */
        if (list_empty(&kthread_create_list))
            schedule();  // 调度其他任务，等待新的线程创建请求
        
        __set_current_state(TASK_RUNNING);  // 将线程状态设置回运行状态

        spin_lock(&kthread_create_lock);  // 获取 kthread 创建请求列表的自旋锁
        
        /* 处理待处理的 kthread 创建请求 */
        while (!list_empty(&kthread_create_list)) {
            struct kthread_create_info *create;

            /* 获取下一个待处理的 kthread 创建请求 */
            create = list_entry(kthread_create_list.next,
                                struct kthread_create_info, list);
            list_del_init(&create->list);  // 从列表中移除该请求并初始化其链接
            
            spin_unlock(&kthread_create_lock);  // 解锁，允许其他线程访问创建请求列表

            /* 根据请求创建并初始化新的 kthread */
            create_kthread(create);

            spin_lock(&kthread_create_lock);  // 获取锁，以处理下一个创建请求
        }
        spin_unlock(&kthread_create_lock);  // 解锁 kthread 创建请求列表
        
        // 回到循环的开头，继续等待和处理线程创建请求
    }

    return 0;  // 实际上永远不会到达这里，因为此循环会无限运行
}
```
这个函数主要干两件事：
    1：schedule();调度线程
    2：create_kthread(create);根据kthread_create_list创建新的线程

