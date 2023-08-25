---
title: process-ksoftirqd
top: false
cover: false
toc: true
mathjax: true
date: 2023-08-25 11:30:32
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

# ksoftirqd线程
`ksoftirqd` 是一个内核线程，用于处理软中断（softirq）。软中断是一种低优先级的中断，与硬件中断（irq）相比，它们的优先级更低，不会直接打断正在执行的内核代码，而是在内核上下文中延迟处理。`ksoftirqd` 线程的主要任务是处理这些软中断。

在Linux内核中，有多种软中断，每种都有不同的用途，例如网络处理、定时器处理、任务延迟等。以下是一些软中断的类型和用途：

1. **NET_RX_SOFTIRQ：** 用于处理网络接收的数据包。当网络接口接收到数据包后，它会触发这个软中断，`ksoftirqd` 线程负责处理和处理这些数据包。

2. **TIMER_SOFTIRQ：** 用于处理定时器事件。当一个定时器到期时，它会触发这个软中断，`ksoftirqd` 线程会执行相应的定时器处理函数。

3. **TASKLET_SOFTIRQ：** 用于执行延迟处理的任务。这是一种低延迟的工作队列机制，用于处理需要在延迟上下文中执行的工作。

4. **HI_SOFTIRQ：** 用于高优先级的软中断处理。这些软中断具有比普通软中断更高的优先级，通常用于处理紧急的任务。

5. **RCU_SOFTIRQ：** 用于执行RCU（Read-Copy-Update）机制的回调。RCU是一种数据同步机制，用于在不阻塞读取操作的情况下更新共享数据结构。

`ksoftirqd` 线程根据软中断的优先级处理这些不同类型的软中断。每个 CPU 内核都有一个对应的 `ksoftirqd` 线程，例如 `ksoftirqd/0` 表示第一个 CPU 的 `ksoftirqd` 线程。这些线程的任务是根据需要处理软中断，以确保内核能够高效地响应各种中断事件。

# ksoftirqd源码
kernel/softirq.c: spawn_ksoftirqd()--->smpboot_register_percpu_thread()--->__smpboot_create_thread()--->kthread_create_on_cpu()--->kthread_create_on_node()--->list_add_tail(&create->list, &kthread_create_list)<---kthread进程
```c
static __init int spawn_ksoftirqd(void)
{
    // 注册 CPU 通知器，以便在 CPU 状态发生变化时进行通知
    register_cpu_notifier(&cpu_nfb);

    // 注册软中断线程
    // 使用 smpboot_register_percpu_thread() 函数在每个 CPU 内核上注册一个软中断线程
    BUG_ON(smpboot_register_percpu_thread(&softirq_threads));

    return 0;
}
// 在早期初始化阶段调用 spawn_ksoftirqd 函数
early_initcall(spawn_ksoftirqd);
```
```c
/**
 * smpboot_register_percpu_thread - 注册与热插拔相关的 per_cpu 线程
 * @plug_thread: 热插拔线程描述符
 *
 * 在所有在线 CPU 上创建并启动线程。
 */
int smpboot_register_percpu_thread(struct smp_hotplug_thread *plug_thread)
{
    unsigned int cpu;
    int ret = 0;

    // 获取在线的 CPU
    get_online_cpus();
    mutex_lock(&smpboot_threads_lock);
    
    // 遍历所有在线的 CPU
    for_each_online_cpu(cpu) {
        // 创建并启动线程
        ret = __smpboot_create_thread(plug_thread, cpu);
        if (ret) {
            // 创建失败，销毁已创建的线程
            smpboot_destroy_threads(plug_thread);
            goto out;
        }
        
        // 启动线程
        smpboot_unpark_thread(plug_thread, cpu);
    }
    
    // 将线程描述符添加到热插拔线程列表
    list_add(&plug_thread->list, &hotplug_threads);

out:
    mutex_unlock(&smpboot_threads_lock);
    // 释放在线 CPU
    put_online_cpus();
    return ret;
}
EXPORT_SYMBOL_GPL(smpboot_register_percpu_thread);
```
```c
static int
__smpboot_create_thread(struct smp_hotplug_thread *ht, unsigned int cpu)
{
    struct task_struct *tsk = *per_cpu_ptr(ht->store, cpu);
    struct smpboot_thread_data *td;

    // 如果在该 CPU 上已经存在一个任务（线程），则不需要再创建
    if (tsk)
        return 0;

    // 为 smpboot_thread_data 结构体分配内存并初始化为零
    td = kzalloc_node(sizeof(*td), GFP_KERNEL, cpu_to_node(cpu));
    if (!td)
        return -ENOMEM;
    td->cpu = cpu;
    td->ht = ht;

    // 在指定的 CPU 上创建内核线程，使用 smpboot_thread_fn 作为线程函数
    tsk = kthread_create_on_cpu(smpboot_thread_fn, td, cpu, ht->thread_comm);
    if (IS_ERR(tsk)) {
        // 创建失败，释放分配的内存并返回错误代码
        kfree(td);
        return PTR_ERR(tsk);
    }

    // 增加线程的引用计数
    get_task_struct(tsk);
    // 将线程指针保存到指定 CPU 的 ht->store 中
    *per_cpu_ptr(ht->store, cpu) = tsk;

    if (ht->create) {
        /*
         * 确保任务实际上已经进入了停放位置，然后再调用创建回调函数。
         * 至少迁移线程回调要求任务已经离开了运行队列。
         */
        if (!wait_task_inactive(tsk, TASK_PARKED))
            WARN_ON(1); // 若未成功进入停放状态，则发出警告
        else
            ht->create(cpu); // 执行创建回调函数
    }

    return 0;
}
```
```c
/**
 * kthread_create_on_cpu - 在指定 CPU 上创建内核线程
 * @threadfn: 线程函数
 * @data: 传递给线程函数的数据指针
 * @cpu: 要创建线程的目标 CPU
 * @namefmt: 线程名称的格式字符串
 *
 * 在指定的 CPU 上创建一个内核线程。
 * 
 * 返回：指向新创建线程的 task_struct 结构体指针，或者错误指针。
 */
struct task_struct *kthread_create_on_cpu(int (*threadfn)(void *data),
                                          void *data, unsigned int cpu,
                                          const char *namefmt)
{
    struct task_struct *p;

    // 在指定的 NUMA 节点上创建内核线程
    p = kthread_create_on_node(threadfn, data, cpu_to_node(cpu), namefmt,
                               cpu);
    if (IS_ERR(p))
        return p;

    // 设置线程为 per_cpu 线程，标志位 KTHREAD_IS_PER_CPU
    set_bit(KTHREAD_IS_PER_CPU, &to_kthread(p)->flags);
    // 设置线程的 CPU 属性
    to_kthread(p)->cpu = cpu;
    /* 将线程停放以将其从 TASK_UNINTERRUPTIBLE 状态移出 */
    kthread_park(p);
    return p;
}
```

```c
/**
 * kthread_create_on_node - 在指定 NUMA 节点上创建内核线程
 * @threadfn: 线程函数
 * @data: 传递给线程函数的数据指针
 * @node: 要创建线程的目标 NUMA 节点
 * @namefmt: 线程名称的格式字符串
 * @...: 可变参数列表
 *
 * 在指定的 NUMA 节点上创建一个内核线程。此函数会创建一个 kthread_create_info 结构体，
 * 初始化线程相关的信息，并将线程请求添加到 kthread_create_list 中，然后唤醒 kthreadd_task
 * 来处理线程的创建。
 * 
 * 返回：指向新创建线程的 task_struct 结构体指针，或者错误指针。
 */
struct task_struct *kthread_create_on_node(int (*threadfn)(void *data),
                                           void *data, int node,
                                           const char namefmt[],
                                           ...)
{
    DECLARE_COMPLETION_ONSTACK(done);
    struct task_struct *task;
    struct kthread_create_info *create = kmalloc(sizeof(*create), GFP_KERNEL);

    if (!create)
        return ERR_PTR(-ENOMEM);
    create->threadfn = threadfn;
    create->data = data;
    create->node = node;
    create->done = &done;

    spin_lock(&kthread_create_lock);
    // 将线程创建请求添加到 kthread_create_list 中
    list_add_tail(&create->list, &kthread_create_list);
    spin_unlock(&kthread_create_lock);

    // 唤醒 kthreadd_task 来处理线程的创建
    wake_up_process(kthreadd_task);
    /*
     * 在可终止状态下等待完成，因为可能会在 kthreadd 尝试为新内核线程分配内存时
     * 被 OOM 杀手选择。
     */
    if (unlikely(wait_for_completion_killable(&done))) {
        /*
         * 如果在 kthreadd（或新内核线程）调用 complete() 之前收到 SIGKILL 信号，
         * 则将对此结构体的清理留给那个线程。
         */
        if (xchg(&create->done, NULL))
            return ERR_PTR(-EINTR);
        /*
         * kthreadd（或新内核线程）将会很快调用 complete()。
         */
        wait_for_completion(&done);
    }
    task = create->result;
    if (!IS_ERR(task)) {
        static const struct sched_param param = { .sched_priority = 0 };
        va_list args;

        va_start(args, namefmt);
        vsnprintf(task->comm, sizeof(task->comm), namefmt, args);
        va_end(args);
        /*
         * root 可能会更改我们（kthreadd 的）优先级或 CPU 掩码。
         * 内核线程不应继承这些属性。
         */
        sched_setscheduler_nocheck(task, SCHED_NORMAL, &param);
        set_cpus_allowed_ptr(task, cpu_all_mask);
    }
    kfree(create);
    return task;
}
EXPORT_SYMBOL(kthread_create_on_node);
```
list_add_tail(&create->list, &kthread_create_list)就是将每个cpu创建一个软中断并添加到kthread_create_list链表中，由kthread线程初始化。所以你的ps -A --forest会出现ksoftirqd/x。

# softirq函数
run_ksoftirqd()--->__do_softirq()--->softirq_vec[...].actions--->用户注册的软中断
```c
static struct smp_hotplug_thread softirq_threads = {
	.store			= &ksoftirqd,
	.thread_should_run	= ksoftirqd_should_run,
	.thread_fn		= run_ksoftirqd,
	.thread_comm		= "ksoftirqd/%u",
};
```
传递给kthread创建的线程结构体
```c
/**
 * run_ksoftirqd - 在指定 CPU 上运行软中断处理程序
 * @cpu: 目标 CPU 的编号
 *
 * 在给定的 CPU 上运行软中断（softirq）处理程序，用于处理一些低优先级的中断任务。
 * 
 * 该函数会先禁用本地中断，然后检查是否有待处理的软中断。如果有，它会调用 __do_softirq() 函数
 * 来运行软中断处理程序，处理各种不同类型的软中断任务。然后，它重新启用本地中断，允许其他中断继续发生。
 * 如果在软中断运行期间需要进行 RCU（Read-Copy-Update）的切换，函数会在必要时调度其他任务，
 * 以确保 RCU 安全切换。
 */
static void run_ksoftirqd(unsigned int cpu)
{
    local_irq_disable(); // 禁用本地中断，确保软中断期间不会被其他中断打断

    if (local_softirq_pending()) {
        /*
         * 我们可以在内联栈上安全运行软中断，
         * 因为我们在这里不深入到任务堆栈中。
         */
        __do_softirq(); // 运行软中断处理程序
        local_irq_enable(); // 重新启用本地中断
        cond_resched_rcu_qs(); // 在需要时调度其他任务以确保 RCU 安全切换
        return;
    }

    local_irq_enable(); // 重新启用本地中断
}
```
```c
/**
 * __do_softirq - 执行软中断处理程序
 *
 * 此函数用于在内核中运行软中断（softirq）的处理程序。软中断是一种低优先级的中断，
 * 用于处理一些延迟敏感但不需要立即响应的任务。该函数负责按顺序执行挂起的软中断，
 * 并在处理每个软中断时调用相应的处理函数。
 */
asmlinkage __visible void __do_softirq(void)
{
    // 计算软中断处理的最大时间
    unsigned long end = jiffies + MAX_SOFTIRQ_TIME;
    // 保存旧的任务标志
    unsigned long old_flags = current->flags;
    // 最大允许重新启动次数
    int max_restart = MAX_SOFTIRQ_RESTART;
    // 指向软中断处理程序
    struct softirq_action *h;
    // 是否在硬中断上下文中
    bool in_hardirq;
    // 待处理的软中断位掩码
    __u32 pending;
    // 待处理的软中断位
    int softirq_bit;

    /* 屏蔽 PF_MEMALLOC，因为当前任务上下文被借用用于软中断处理。 */
    current->flags &= ~PF_MEMALLOC;

    // 获取待处理的软中断位掩码
    pending = local_softirq_pending();
    // 记录进入软中断处理的时间
    account_irq_enter_time(current);

    // 关闭本地底半部中断，开始软中断处理
    __local_bh_disable_ip(_RET_IP_, SOFTIRQ_OFFSET);
    // 开始跟踪软中断
    in_hardirq = lockdep_softirq_start();

restart:
    // 在启用 IRQ 之前重置挂起的位掩码
    set_softirq_pending(0);

    // 启用本地中断
    local_irq_enable();

    // 获取软中断处理程序向量的起始地址
    h = softirq_vec;

    // 逐个处理待处理的软中断
    while ((softirq_bit = ffs(pending))) {
        unsigned int vec_nr;
        int prev_count;

        // 选择要处理的软中断
        h += softirq_bit - 1;
        // 获取软中断号
        vec_nr = h - softirq_vec;
        // 保存进入软中断前的抢占计数
        prev_count = preempt_count();

        // 增加本 CPU 上的软中断计数
        kstat_incr_softirqs_this_cpu(vec_nr);

        // 跟踪软中断进入
        trace_softirq_entry(vec_nr);
        // 调用软中断处理函数
        h->action(h);
        // 跟踪软中断退出
        trace_softirq_exit(vec_nr);
        
        // 检查软中断期间抢占计数的变化
        if (unlikely(prev_count != preempt_count())) {
            pr_err("huh, entered softirq %u %s %p with preempt_count %08x, exited with %08x?\n",
                   vec_nr, softirq_to_name[vec_nr], h->action,
                   prev_count, preempt_count());
            preempt_count_set(prev_count);
        }
        // 移动到下一个软中断
        h++;
        // 清除已处理的软中断位
        pending >>= softirq_bit;
    }

    // 在软中断处理完成后，执行 RCU 切换
    rcu_bh_qs();
    // 关闭本地中断
    local_irq_disable();

    // 再次获取待处理的软中断位掩码
    pending = local_softirq_pending();
    // 如果仍有未处理的软中断
    if (pending) {
        // 如果尚未超过最大处理时间，并且不需要任务调度，并且还可以重新尝试处理
        if (time_before(jiffies, end) && !need_resched() && --max_restart)
            goto restart;

        // 唤醒软中断线程（ksoftirqd）
        wakeup_softirqd();
    }

    // 结束软中断处理
    lockdep_softirq_end(in_hardirq);
    // 记录退出软中断处理的时间
    account_irq_exit_time(current);
    // 启用底半部中断
    __local_bh_enable(SOFTIRQ_OFFSET);
    // 在软中断处理后，不应该仍处于硬中断上下文中
    WARN_ON_ONCE(in_interrupt());
    // 恢复任务的标志和状态
    tsk_restore_flags(current, old_flags, PF_MEMALLOC);
}
```
```c
static struct softirq_action softirq_vec[NR_SOFTIRQS] __cacheline_aligned_in_smp;
```
kernel/softirq.c定义了一个数组 `softirq_vec`，用于存储软中断（softirq）处理程序的函数指针。逐步解释其中的每个部分：

1. `static`：这个关键字指示变量 `softirq_vec` 的作用范围仅限于当前文件。它是一个静态变量，意味着其生命周期从程序启动到终止，不会在不同的函数调用之间失去其值。

2. `struct softirq_action`：这是一个结构体类型，用于存储软中断处理程序的信息。它包含了一个函数指针 `action`，指向一个具体的软中断处理函数。

3. `softirq_vec[NR_SOFTIRQS]`：这是一个数组，长度为 `NR_SOFTIRQS`，它定义了一个能够容纳多个软中断处理程序的存储空间。每个元素都是一个 `struct softirq_action` 类型的结构体，其中存储了软中断处理函数的指针。

4. `__cacheline_aligned_in_smp`：这个属性指示编译器在 SMP（对称多处理器）系统上，将 `softirq_vec` 数据结构对齐到 CPU 缓存行的边界，以提高访问性能。这是一种优化，可以减少因为不必要的缓存行填充而造成的性能损失。

`softirq_vec`，用于存储软中断处理程序的函数指针。每个软中断在数组中对应一个元素，该元素包含了指向具体软中断处理函数的指针。这种机制允许内核注册多个不同类型的软中断处理程序，并在适当的时候调用这些函数来执行相应的任务。