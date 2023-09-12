---
title: process-kworker
top: false
cover: false
toc: true
mathjax: true
date: 2023-08-25 14:11:57
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

# kworker线程
`kworker` 是一类内核线程，用于执行一些与内核相关的后台任务。这些线程被用于处理一些异步工作，以避免阻塞主线程或其他关键内核线程。`kworker` 线程通常不与用户空间交互，而是专注于内核级别的任务。

主要特点和用途：

1. **后台任务处理**：`kworker` 线程主要用于处理一些后台任务，如延迟的工作队列、定时器、中断处理等。

2. **异步执行**：它们允许内核在不同的上下文中执行一些工作，而不会干扰到主线程或其他关键的内核线程。

3. **并发性能优化**：在多核系统中，`kworker` 线程可以并行执行，从而提高系统的并发性能。

4. **避免阻塞**：`kworker` 线程通常用于处理一些可能会阻塞主线程的工作，以确保内核的响应性不受影响。

5. **调度策略**：它们可以使用不同的调度策略，以便在不同的上下文中执行任务，而不会竞争其他关键任务的资源。

`kworker` 线程是一种在内核中用于执行后台任务的机制，有助于提高系统的性能和响应性。这些线程的设计允许内核在不同的上下文中执行任务，从而保持系统的平稳运行。不同的内核版本和配置可能会有不同数量的 `kworker` 线程，以适应系统的需求。

# kworker源码
kernel/workqueue.c：init_workqueues()--->create_worker()--->kthread_create_on_node()<---kthread进程
```c
/**
 * init_workqueues - 初始化工作队列
 *
 * 这个函数在内核启动过程中被调用，用于初始化工作队列相关的数据结构和参数。
 * 工作队列是内核中用于处理异步任务的机制，它允许后台任务在不阻塞主要线程的情况下执行。
 */
static int __init init_workqueues(void)
{
    // 各个工作队列池的标准优先级设置
    int std_nice[NR_STD_WORKER_POOLS] = { 0, HIGHPRI_NICE_LEVEL };
    int i, cpu;

    // 检查结构体对齐，确保池子工作队列和 long long 类型对齐
    WARN_ON(__alignof__(struct pool_workqueue) < __alignof__(long long));

    // 初始化工作队列池缓存
    pwq_cache = KMEM_CACHE(pool_workqueue, SLAB_PANIC);

    // 注册 CPU 通知回调，用于处理 CPU 的上线事件
    cpu_notifier(workqueue_cpu_up_callback, CPU_PRI_WORKQUEUE_UP);
    // 注册 CPU 热移除通知回调，用于处理 CPU 的下线事件
    hotcpu_notifier(workqueue_cpu_down_callback, CPU_PRI_WORKQUEUE_DOWN);

    // 初始化 NUMA 相关设置
    wq_numa_init();

    // 初始化 CPU 池子
    for_each_possible_cpu(cpu) {
        struct worker_pool *pool;

        i = 0;
        for_each_cpu_worker_pool(pool, cpu) {
            // 初始化池子工作队列
            BUG_ON(init_worker_pool(pool));
            pool->cpu = cpu;
            cpumask_copy(pool->attrs->cpumask, cpumask_of(cpu));
            pool->attrs->nice = std_nice[i++];
            pool->node = cpu_to_node(cpu);

            /* 分配池子 ID */
            mutex_lock(&wq_pool_mutex);
            BUG_ON(worker_pool_assign_id(pool));
            mutex_unlock(&wq_pool_mutex);
        }
    }

    // 创建初始工作者
    for_each_online_cpu(cpu) {
        struct worker_pool *pool;

        for_each_cpu_worker_pool(pool, cpu) {
            pool->flags &= ~POOL_DISASSOCIATED;
            BUG_ON(!create_worker(pool));
        }
    }

    // 创建默认的 unbound 和 ordered 工作队列属性
    for (i = 0; i < NR_STD_WORKER_POOLS; i++) {
        struct workqueue_attrs *attrs;

        // 分配工作队列属性
        BUG_ON(!(attrs = alloc_workqueue_attrs(GFP_KERNEL)));
        attrs->nice = std_nice[i];
        unbound_std_wq_attrs[i] = attrs;

        /*
         * 有序工作队列只应有一个 pwq，由 pwqs 强制执行排序。
         * 关闭 NUMA 以便 dfl_pwq 用于所有节点。
         */
        BUG_ON(!(attrs = alloc_workqueue_attrs(GFP_KERNEL)));
        attrs->nice = std_nice[i];
        attrs->no_numa = true;
        ordered_wq_attrs[i] = attrs;
    }

    // 创建系统工作队列
    system_wq = alloc_workqueue("events", 0, 0);
    system_highpri_wq = alloc_workqueue("events_highpri", WQ_HIGHPRI, 0);
    system_long_wq = alloc_workqueue("events_long", 0, 0);
    system_unbound_wq = alloc_workqueue("events_unbound", WQ_UNBOUND,
                                        WQ_UNBOUND_MAX_ACTIVE);
    system_freezable_wq = alloc_workqueue("events_freezable",
                                          WQ_FREEZABLE, 0);
    system_power_efficient_wq = alloc_workqueue("events_power_efficient",
                                                WQ_POWER_EFFICIENT, 0);
    system_freezable_power_efficient_wq = alloc_workqueue("events_freezable_power_efficient",
                                                          WQ_FREEZABLE | WQ_POWER_EFFICIENT,
                                                          0);
    // 检查系统工作队列是否成功创建
    BUG_ON(!system_wq || !system_highpri_wq || !system_long_wq ||
           !system_unbound_wq || !system_freezable_wq ||
           !system_power_efficient_wq ||
           !system_freezable_power_efficient_wq);
    return 0;
}
// 在内核初始化阶段调用 init_workqueues 函数
early_initcall(init_workqueues);
```
```c
/**
 * create_worker - 创建一个新的工作队列工作者
 * @pool: 新工作者将属于的池子
 *
 * 这个函数用于创建并启动一个新的工作队列工作者，该工作者将附属于指定的池子 @pool。
 *
 * 上下文：
 * 这个函数可能会进行休眠操作（可能会分配内存，可能会导致调度器切换）。
 *
 * 返回：
 * 返回指向新创建的工作者的指针，如果创建失败则返回 NULL。
 */
static struct worker *create_worker(struct worker_pool *pool)
{
    struct worker *worker = NULL;  // 初始化工作者指针
    int id = -1;  // 初始化工作者的 ID
    char id_buf[16];  // 用于存储 ID 的字符缓冲区

    // 获取一个唯一的工作者 ID
    id = ida_simple_get(&pool->worker_ida, 0, 0, GFP_KERNEL);
    if (id < 0)
        goto fail;

    // 分配工作者的内存
    worker = alloc_worker(pool->node);
    if (!worker)
        goto fail;

    // 初始化工作者的属性
    worker->pool = pool;
    worker->id = id;

    // 创建工作者的线程名
    if (pool->cpu >= 0)
        snprintf(id_buf, sizeof(id_buf), "%d:%d%s", pool->cpu, id,
                 pool->attrs->nice < 0  ? "H" : "");
    else
        snprintf(id_buf, sizeof(id_buf), "u%d:%d", pool->id, id);

    // 在指定的 NUMA 节点上创建工作者线程
    worker->task = kthread_create_on_node(worker_thread, worker, pool->node,
                                          "kworker/%s", id_buf);
    if (IS_ERR(worker->task))
        goto fail;

    // 设置工作者线程的优先级
    set_user_nice(worker->task, pool->attrs->nice);

    // 防止用户干扰工作者线程的 CPU 亲和性设置
    worker->task->flags |= PF_NO_SETAFFINITY;

    // 将工作者附加到池子
    worker_attach_to_pool(worker, pool);

    // 启动新创建的工作者线程
    spin_lock_irq(&pool->lock);
    worker->pool->nr_workers++;
    worker_enter_idle(worker);
    wake_up_process(worker->task);
    spin_unlock_irq(&pool->lock);

    return worker;  // 返回新创建的工作者指针

fail:
    if (id >= 0)
        ida_simple_remove(&pool->worker_ida, id);  // 清理 ID 分配
    kfree(worker);  // 释放工作者内存
    return NULL;  // 返回 NULL 表示创建失败
}
```
根据工作者所属的池子属性来为工作者线程生成一个名称。生成的名称将包含一些池子和工作者的信息，以便在内核中识别工作者线程的用途。具体的命名方式如下：

- 如果 `pool->cpu >= 0`，即工作者线程分配到了特定的 CPU，则名称将按以下格式生成：
  - `%d:%d` 用于表示池子所在的 CPU 编号和工作者的 ID
  - `%s` 根据池子的属性 `pool->attrs->nice`，如果优先级小于 0（HIGHPRI_NICE_LEVEL），则附加 "H"，表示高优先级

- 如果 `pool->cpu` 小于 0，即工作者线程是无绑定到特定 CPU 的，则名称将按以下格式生成：
  - `u%d:%d` 用于表示池子的 ID 和工作者的 ID

例如，如果 `pool->cpu` 是 2，`id` 是 5，并且 `pool->attrs->nice` 为正值，则生成的名称可能是 "2:5"。如果 `pool->cpu` 是 -1，`pool->id` 是 1，`id` 是 3，则生成的名称可能是 "u1:3"。

这个命名方式是为了在内核中更好地识别不同的工作者线程以及它们所属的池子和属性。这对于调试和监控工作者线程的活动非常有帮助。

# kworker函数
worker_thread()--->process_scheduled_works()--->process_one_work()
```c
/**
 * worker_thread - 工作者线程函数
 * @__worker: 自身工作者
 *
 * 工作者线程函数。所有工作者都属于一个工作者池（worker_pool） - 可能是每个 CPU 的一个或动态的无绑定池。这些工作者处理所有工作项，不管它们的特定目标工作队列。唯一的例外是属于具有救援者（rescuer）的工作队列的工作项，这将在 rescuer_thread() 中解释。

 * 返回值：0
 */
static int worker_thread(void *__worker)
{
	struct worker *worker = __worker;
	struct worker_pool *pool = worker->pool;

	// 告诉调度器这是一个工作队列工作者
	worker->task->flags |= PF_WQ_WORKER;

woke_up:
	spin_lock_irq(&pool->lock);

	// 是否应该终止？
	if (unlikely(worker->flags & WORKER_DIE)) {
		spin_unlock_irq(&pool->lock);
		
		// 确保 worker 不在任何列表中
		WARN_ON_ONCE(!list_empty(&worker->entry));

		// 清除工作者标志
		worker->task->flags &= ~PF_WQ_WORKER;

		// 设置任务的名称为 "kworker/dying"
		set_task_comm(worker->task, "kworker/dying");

		// 从工作者池的 worker_ida 中移除工作者 ID
		ida_simple_remove(&pool->worker_ida, worker->id);

		// 从工作者池中分离工作者
		worker_detach_from_pool(worker, pool);

		// 释放工作者内存
		kfree(worker);
		return 0;
	}

	// 让工作者离开空闲状态，准备处理工作
	worker_leave_idle(worker);

recheck:
	// 是否不再需要更多工作者？
	if (!need_more_worker(pool))
		goto sleep;

	// 是否需要进行管理？
	if (unlikely(!may_start_working(pool)) && manage_workers(worker))
		goto recheck;

	/*
	 * ->scheduled 列表只能在工作者准备处理工作或实际处理工作时填充。
	 * 确保在休眠时没有人干扰它。
	 */
	WARN_ON_ONCE(!list_empty(&worker->scheduled));

	/*
	 * 完成 PREP 阶段。我们保证至少有一个空闲工作者或其他人已经承担了管理者角色。
	 * 如果适用，这是 @worker 开始参与并发管理的地方，并在重新绑定后恢复并发管理。
	 * 有关详细信息，请参阅 rebind_workers()。
	 */
	worker_clr_flags(worker, WORKER_PREP | WORKER_REBOUND);

	do {
		struct work_struct *work =
			list_first_entry(&pool->worklist,
					 struct work_struct, entry);

		if (likely(!(*work_data_bits(work) & WORK_STRUCT_LINKED))) {
			/* 优化路径，不是严格必需的 */
			process_one_work(worker, work);
			if (unlikely(!list_empty(&worker->scheduled)))
				process_scheduled_works(worker);
		} else {
			move_linked_works(work, &worker->scheduled, NULL);
			process_scheduled_works(worker);
		}
	} while (keep_working(pool));

	// 设置工作者为准备状态
	worker_set_flags(worker, WORKER_PREP);

sleep:
	/*
	 * 池->lock 已经持有，没有要处理的工作也没有必要管理，进入休眠。
	 * 工作者只在持有池->lock 或从本地 CPU 中唤醒时被唤醒，因此在释放池->lock 之前设置当前状态足以防止丢失任何事件。
	 */
	worker_enter_idle(worker);
	
	// 设置当前线程状态为可中断睡眠
	__set_current_state(TASK_INTERRUPTIBLE);
	spin_unlock_irq(&pool->lock);

	// 进入调度器，等待被唤醒
	schedule();
	goto woke_up;
}
```
```c
/**
 * process_scheduled_works - 处理预定的工作项
 * @worker: 自身工作者
 *
 * 处理所有预定的工作项。请注意，预定的工作项列表在处理工作项时可能会发生变化，因此此函数反复从顶部获取工作项并执行它们。

 * 上下文：
 * 在 spin_lock_irq(pool->lock) 下，可能会多次释放和重新获取锁。
 */
static void process_scheduled_works(struct worker *worker)
{
	while (!list_empty(&worker->scheduled)) {
		struct work_struct *work = list_first_entry(&worker->scheduled,
						struct work_struct, entry);
		process_one_work(worker, work);
	}
}
```
```c
/**
 * process_one_work - 处理单个工作项
 * @worker: 自身工作者
 * @work: 要处理的工作项
 *
 * 处理 @work。此函数包含处理单个工作项所需的所有逻辑，包括与同一 CPU 上的其他工作者的同步和交互、排队和刷新。只要满足上下文要求，任何工作者都可以调用此函数来处理工作项。

 * 上下文：
 * 在 spin_lock_irq(pool->lock) 下，会释放并重新获取锁。
 */
static void process_one_work(struct worker *worker, struct work_struct *work)
__releases(&pool->lock)
__acquires(&pool->lock)
{
	struct pool_workqueue *pwq = get_work_pwq(work);
	struct worker_pool *pool = worker->pool;
	bool cpu_intensive = pwq->wq->flags & WQ_CPU_INTENSIVE;
	int work_color;
	struct worker *collision;
#ifdef CONFIG_LOCKDEP
	/*
	 * 可以在从工作项调用的函数内部释放 struct work_struct，因此我们也需要在 lockdep 中考虑这一点。为了避免虚假的“已持有的锁被释放”警告，
	 * 以及在查看 work->lockdep_map 时出现问题，我们在这里创建一个副本并使用它。
	 */
	struct lockdep_map lockdep_map;

	lockdep_copy_map(&lockdep_map, &work->lockdep_map);
#endif
	/* 确保我们在正确的 CPU 上 */
	WARN_ON_ONCE(!(pool->flags & POOL_DISASSOCIATED) &&
		     raw_smp_processor_id() != pool->cpu);

	/*
	 * 一个工作项不应在单个 CPU 上的多个工作者之间并发执行。
	 * 检查是否有其他工作者已经在处理这个工作项。如果是这样，则将工作项推迟到当前正在执行的工作者。
	 */
	collision = find_worker_executing_work(pool, work);
	if (unlikely(collision)) {
		move_linked_works(work, &collision->scheduled, NULL);
		return;
	}

	/* 认领并出队 */
	debug_work_deactivate(work);
	hash_add(pool->busy_hash, &worker->hentry, (unsigned long)work);
	worker->current_work = work;
	worker->current_func = work->func;
	worker->current_pwq = pwq;
	work_color = get_work_color(work);

	list_del_init(&work->entry);

	/*
	 * CPU 密集型的工作项不参与并发管理。它们由调度器负责。
	 * 这将把 @worker 从并发管理中移出，并且下一个代码块将链接执行挂起的工作项。
	 */
	if (unlikely(cpu_intensive))
		worker_set_flags(worker, WORKER_CPU_INTENSIVE);

	/*
	 * 如果需要的话唤醒另一个工作者。对于正常的每个 CPU 工作者，条件始终为 false，因为 nr_running 在此时总是 >= 1。
	 * 这用于链接执行挂起的工作项，对于 WORKER_NOT_RUNNING 工作者（如 UNBOUND 和 CPU_INTENSIVE）。
	 */
	if (need_more_worker(pool))
		wake_up_worker(pool);

	/*
	 * 记录最后一个工作池并清除 PENDING，这应该是对 @work 的最后一次更新。
	 * 同时，这在 @pool->lock 中完成，以便在禁用 IRQ 时同时发生 PENDING 和队列状态的变化。
	 */
	set_work_pool_and_clear_pending(work, pool->id);

	spin_unlock_irq(&pool->lock);

	lock_map_acquire_read(&pwq->wq->lockdep_map);
	lock_map_acquire(&lockdep_map);
	trace_workqueue_execute_start(work);
	worker->current_func(work);
	/*
	 * 虽然我们必须小心，以免在此之后使用“work”，但跟踪点只会记录其地址。
	 */
	trace_workqueue_execute_end(work);
	lock_map_release(&lockdep_map);
	lock_map_release(&pwq->wq->lockdep_map);

	if (unlikely(in_atomic() || lockdep_depth(current) > 0)) {
		pr_err("BUG: workqueue leaked lock or atomic: %s/0x%08x/%d\n"
		       "     last function: %pf\n",
		       current->comm, preempt_count(), task_pid_nr(current),
		       worker->current_func);
		debug_show_held_locks(current);
		dump_stack();
	}

	/*
	 * 以下内容可以防止 kworker 在没有 PREEMPT 的内核上占用 CPU，
	 * 在这种情况下，等待重新排队的工作项等待某些事情发生可能会与 stop_machine 死锁，
	 * 因为这种工作项可以无限期地重新排队自己，而所有其他 CPU 都被困在 stop_machine 中。
	 * 同时，报告一个静止的 RCU 状态，以便相同的条件不会冻结 RCU。
	 */
	cond_resched_rcu_qs();

	spin_lock_irq(&pool->lock);

	/* 清除 CPU 密集状态 */
	if (unlikely(cpu_intensive))
		worker_clr_flags(worker, WORKER_CPU_INTENSIVE);

	/* 我们已经完成了它，释放 */
	hash_del(&worker->hentry);
	worker->current_work = NULL;
	worker->current_func = NULL;
	worker->current_pwq = NULL;
	worker->desc_valid = false;
	pwq_dec_nr_in_flight(pwq, work_color);
}
```
# ps -A --forest 
```c
ps -A --forest
  PID TTY          TIME CMD
    2 ?        00:00:00 kthreadd
    3 ?        00:00:01  \_ ksoftirqd/0
    5 ?        00:00:00  \_ kworker/0:0H
    7 ?        00:00:06  \_ rcu_preempt
    8 ?        00:00:00  \_ rcu_sched
    9 ?        00:00:00  \_ rcu_bh
   10 ?        00:00:00  \_ migration/0
   11 ?        00:00:00  \_ khelper
   12 ?        00:00:00  \_ kdevtmpfs
   13 ?        00:00:00  \_ perf
   14 ?        00:00:00  \_ writeback
   15 ?        00:00:00  \_ crypto
   16 ?        00:00:00  \_ bioset
   17 ?        00:00:00  \_ kblockd
   18 ?        00:00:00  \_ ata_sff
   20 ?        00:00:00  \_ cfg80211
   21 ?        00:00:00  \_ rpciod
   22 ?        00:00:00  \_ kswapd0
   23 ?        00:00:00  \_ fsnotify_mark
   24 ?        00:00:00  \_ nfsiod
   61 ?        00:00:00  \_ kapmd
   62 ?        00:00:00  \_ spi2
   63 ?        00:00:00  \_ kworker/u2:1
   68 ?        00:00:00  \_ ci_otg
   70 ?        00:00:00  \_ goodix_wq
   71 ?        00:00:00  \_ cfinteractive
   72 ?        00:00:00  \_ irq/224-mmc0
   73 ?        00:00:00  \_ irq/49-2190000.
   74 ?        00:00:00  \_ mxs_dcp_chan/sh
   75 ?        00:00:00  \_ mxs_dcp_chan/ae
   81 ?        00:00:00  \_ kworker/u2:3
   82 ?        00:00:00  \_ ipv6_addrconf
   83 ?        00:00:00  \_ krfcommd
   84 ?        00:00:00  \_ pxp_dispatch
   85 ?        00:00:00  \_ deferwq
   86 ?        00:00:00  \_ irq/204-imx_the
   87 ?        00:00:00  \_ ubi_bgt0d
  140 ?        00:00:00  \_ ubifs_bgt0_0
 1037 ?        00:00:00  \_ kworker/0:0
 1041 ?        00:00:00  \_ kworker/0:2
 1042 ?        00:00:00  \_ kworker/0:1
```
kworker/x_x即是你的工作线程
