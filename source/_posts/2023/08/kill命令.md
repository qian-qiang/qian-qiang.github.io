---
title: kill命令
top: false
cover: false
toc: true
mathjax: true
date: 2023-08-09 11:32:53
password:
summary:
tags:
- linux
categories:
- linux
keywords:
description:
---

# kill命令是如何执行的
## kill发送信号
文件kernel/signal.c
 ```c
 /**
 *  sys_kill - send a signal to a process
 *  @pid: the PID of the process
 *  @sig: signal to be sent
 */
SYSCALL_DEFINE2(kill, pid_t, pid, int, sig)
{
	struct siginfo info;

	info.si_signo = sig;
	info.si_errno = 0;
	info.si_code = SI_USER;
	info.si_pid = task_tgid_vnr(current);
	info.si_uid = from_kuid_munged(current_user_ns(), current_uid());

	return kill_something_info(sig, &info, pid);
}
 ```
 这段代码是 Linux 内核中实现 `kill` 系统调用的部分。让我们逐步分析这段代码的功能：

1. `SYSCALL_DEFINE2(kill, pid_t, pid, int, sig)`：这是一个宏，用于定义带有两个参数的系统调用 `kill`。`pid_t` 和 `int` 是参数的类型，`pid` 是要发送信号的目标进程的 ID，`sig` 是要发送的信号编号。

2. `struct siginfo info`：这是一个结构体，用于保存信号的附加信息。

3. `info.si_signo = sig`：将信号编号赋值给 `si_signo` 字段，表示要发送的信号的编号。

4. `info.si_errno = 0`：将错误编号字段置为 0，表示没有错误。

5. `info.si_code = SI_USER`：将信号代码字段设置为 `SI_USER`，表示该信号是由用户空间进程发送的。

6. `info.si_pid = task_tgid_vnr(current)`：将当前进程的 TGID（线程组ID）作为发送信号的进程ID。

7. `info.si_uid = from_kuid_munged(current_user_ns(), current_uid())`：将当前进程的有效用户ID转换为用户命名空间中的用户ID，并将结果赋值给发送信号的用户ID字段。

8. `return kill_something_info(sig, &info, pid)`：调用 `kill_something_info` 函数，将信号编号、信号信息结构体和目标进程的ID作为参数传递，并返回结果。这个函数的功能是根据给定的参数发送信号给目标进程。

这段代码实现了 `kill` 系统调用的功能。它接受一个目标进程ID和信号编号作为参数，然后构建一个带有信号信息的结构体，并调用相应的函数将信号发送给目标进程。这是 Linux 内核中管理进程间通信的一部分，允许一个进程向另一个进程发送信号以通知或影响其行为。

 ```c
/*
 * kill_something_info() interprets pid in interesting ways just like kill(2).
 *
 * POSIX specifies that kill(-1,sig) is unspecified, but what we have
 * is probably wrong.  Should make it like BSD or SYSV.
 */

static int kill_something_info(int sig, struct siginfo *info, pid_t pid)
{
	int ret;

	if (pid > 0) {
		rcu_read_lock();
		ret = kill_pid_info(sig, info, find_vpid(pid));
		rcu_read_unlock();
		return ret;
	}

	read_lock(&tasklist_lock);
	if (pid != -1) {
		ret = __kill_pgrp_info(sig, info,
				pid ? find_vpid(-pid) : task_pgrp(current));
	} else {
		int retval = 0, count = 0;
		struct task_struct * p;

		for_each_process(p) {
			if (task_pid_vnr(p) > 1 &&
					!same_thread_group(p, current)) {
				int err = group_send_sig_info(sig, info, p);
				++count;
				if (err != -EPERM)
					retval = err;
			}
		}
		ret = count ? retval : -ESRCH;
	}
	read_unlock(&tasklist_lock);

	return ret;
}
 ```

这段代码是 Linux 内核中用于实现 `kill_something_info` 函数的部分。这个函数用于向一个或多个进程发送信号，具体操作取决于传递的参数。让我们逐步解释这段代码的功能：

1. `static int kill_something_info(int sig, struct siginfo *info, pid_t pid)`：这是一个静态函数，用于发送信号给一个或多个进程。它接受信号编号 `sig`、信号信息结构体 `info` 和目标进程的ID `pid` 作为参数。

2. `if (pid > 0)`：如果目标进程ID大于0，表示要向指定PID的进程发送信号。

   - `rcu_read_lock()`：获取 RCU（Read-Copy-Update）读取锁，确保在读取期间不会发生数据修改。

   - `ret = kill_pid_info(sig, info, find_vpid(pid))`：调用 `kill_pid_info` 函数，向指定的进程发送信号，并传递信号编号、信号信息和目标进程的虚拟PID（vpid）。

   - `rcu_read_unlock()`：释放 RCU 读取锁。

   - 返回 `ret`，表示操作的结果。

3. 如果 `pid` 不大于0：

   - `read_lock(&tasklist_lock)`：获取进程列表读取锁，以确保在遍历进程列表期间不会发生修改。

   - 如果 `pid` 不等于-1，表示要发送信号给指定的进程组：

     - `ret = __kill_pgrp_info(sig, info, pid ? find_vpid(-pid) : task_pgrp(current))`：调用 `__kill_pgrp_info` 函数，向指定的进程组发送信号。如果 `pid` 不为0，表示发送给指定的进程组，否则发送给当前进程组。

   - 否则，表示要向所有非当前线程组中的进程发送信号：

     - `int retval = 0, count = 0;`：初始化变量 `retval` 和 `count`，用于跟踪操作结果和计数。

     - `struct task_struct * p;`：定义一个指向进程结构体的指针。

     - `for_each_process(p)`：遍历所有进程。

       - `if (task_pid_vnr(p) > 1 && !same_thread_group(p, current))`：检查进程的虚拟PID是否大于1（排除init进程和内核线程）以及是否属于与当前进程不同的线程组。

         - `group_send_sig_info(sig, info, p)`：调用 `group_send_sig_info` 函数，向指定进程发送信号。

         - `++count`：递增计数器。

         - 如果返回值不是 `-EPERM`，将 `err` 赋值给 `retval`。

     - `ret = count ? retval : -ESRCH;`：根据计数器判断是否有进程接收到信号，如果有则返回 `retval`，否则返回 `-ESRCH` 表示没有匹配的进程。

   - `read_unlock(&tasklist_lock)`：释放进程列表读取锁。

   - 返回 `ret`，表示操作的结果。

参数 pid 不同取值含义：
⚫ 如果 pid 为正，则信号 sig 将发送到 pid 指定的进程。
⚫ 如果 pid 等于 0，则将 sig 发送到当前进程的进程组中的每个进程。
⚫ 如果 pid 等于-1，则将 sig 发送到当前进程有权发送信号的每个进程，但进程 1（init）除外。
⚫ 如果 pid 小于-1，则将 sig 发送到 ID 为-pid 的进程组中的每个进程。
进程中将信号发送给另一个进程是需要权限的，并不是可以随便给任何一个进程发送信号，超级用户
root 进程可以将信号发送给任何进程，但对于非超级用户（普通用户）进程来说，其基本规则是发送者进程
的实际用户 ID 或有效用户 ID 必须等于接收者进程的实际用户 ID 或有效用户 ID。

## 信号传输的途径
 ```c
int kill_pid_info(int sig, struct siginfo *info, struct pid *pid)
{
	int error = -ESRCH;
	struct task_struct *p;

	for (;;) {
		rcu_read_lock();
		p = pid_task(pid, PIDTYPE_PID);
		if (p)
			error = group_send_sig_info(sig, info, p);
		rcu_read_unlock();
		if (likely(!p || error != -ESRCH))
			return error;

		/*
		 * The task was unhashed in between, try again.  If it
		 * is dead, pid_task() will return NULL, if we race with
		 * de_thread() it will find the new leader.
		 */
	}
}
 ```
这段代码实现了 `kill_pid_info` 函数，它用于向指定的进程发送信号，并且会不断尝试直到发送成功或者出现错误。让我们逐步解释这段代码的功能：

1. `int kill_pid_info(int sig, struct siginfo *info, struct pid *pid)`：这个函数用于向指定的进程发送信号。它接受信号编号 `sig`、信号信息结构体 `info` 和指向目标进程 `struct pid` 的指针作为参数。

2. `int error = -ESRCH;`：初始化错误码为 `-ESRCH`，表示最初的状态是没有找到匹配的进程。

3. `struct task_struct *p;`：定义一个指向进程结构体的指针。

4. `for (;;) {`：进入无限循环，直到发送成功或出现错误。

   - `rcu_read_lock();`：获取 RCU 读取锁。

   - `p = pid_task(pid, PIDTYPE_PID);`：通过给定的 `struct pid` 和 `PIDTYPE_PID` 类型，获取与该PID相关联的进程的指针。

   - `if (p)`：如果找到了相关的进程。

     - `error = group_send_sig_info(sig, info, p);`：调用 `group_send_sig_info` 函数，向指定的进程发送信号，将结果保存在 `error` 中。

   - `rcu_read_unlock();`：释放 RCU 读取锁。

   - `if (likely(!p || error != -ESRCH))`：如果找不到相关进程，或者已经成功发送了信号，跳出循环。

     - `return error;`：返回错误码。

   - 如果进程不在哈希表中，很可能在 `pid_task` 调用期间被取消注册（unhashed），进程结构体可能已经不再可用。

     - 循环重新开始，进行新一轮的尝试。

   这个无限循环会不断尝试发送信号，直到成功发送信号给目标进程或出现错误。如果进程在循环中被取消注册，将会继续尝试直到进程结构体可用。

这段代码实现了一个循环发送信号给指定进程的过程，如果目标进程存在，则发送信号并返回结果，如果目标进程不存在或出现错误，则会不断尝试直到发送成功或者出现无法恢复的错误。

 ```c
 int group_send_sig_info(int sig, struct siginfo *info, struct task_struct *p)
{
	int ret;

	rcu_read_lock();
	ret = check_kill_permission(sig, info, p);
	rcu_read_unlock();

	if (!ret && sig)
		ret = do_send_sig_info(sig, info, p, true);

	return ret;
}
 ```

这段代码执行了以下操作：

1. `rcu_read_lock();`：获取RCU（Read-Copy-Update）读取锁，确保在读取期间不会发生数据修改。

2. `ret = check_kill_permission(sig, info, p);`：调用 `check_kill_permission` 函数，检查是否具有权限向进程组中的进程发送信号，并将结果保存在 `ret` 变量中。

3. `rcu_read_unlock();`：释放RCU读取锁，允许其他线程继续操作。

4. `if (!ret && sig)`：如果没有权限问题（`ret` 为0）且信号编号不为0（表示有信号需要发送）。

   - `ret = do_send_sig_info(sig, info, p, true);`：调用 `do_send_sig_info` 函数，向进程组中的所有进程发送信号，将结果保存在 `ret` 中。

5. 返回 `ret`，表示信号发送操作的结果。

这段代码的目标是向一个进程组中的所有进程发送信号。在执行之前，它会检查是否具有足够的权限来发送信号。然后，如果有信号需要发送，它会调用 `do_send_sig_info` 函数来实际执行信号发送操作。

 ```c
int do_send_sig_info(int sig, struct siginfo *info, struct task_struct *p,
			bool group)
{
	unsigned long flags;
	int ret = -ESRCH;

	if (lock_task_sighand(p, &flags)) {
		ret = send_signal(sig, info, p, group);
		unlock_task_sighand(p, &flags);
	}

	return ret;
}
 ```
`do_send_sig_info` 函数，用于向一个特定进程发送信号，并且可以选择是否发送给整个进程组：

1. `int do_send_sig_info(int sig, struct siginfo *info, struct task_struct *p, bool group)`：这个函数用于向指定的进程发送信号，可以选择是否发送给整个进程组。它接受信号编号 `sig`、信号信息结构体 `info`、目标进程结构体 `p`，以及一个布尔值 `group` 作为参数。

2. `unsigned long flags;`：定义一个无符号长整型变量，用于保存中断标志。

3. `int ret = -ESRCH;`：初始化结果变量为 `-ESRCH`，表示最初状态下信号发送操作没有成功。

4. `if (lock_task_sighand(p, &flags))`：如果成功获取目标进程的信号处理锁。

   - `lock_task_sighand` 会锁定进程的信号处理数据结构，以确保在发送信号的过程中没有其他线程干扰。

5. `ret = send_signal(sig, info, p, group);`：调用 `send_signal` 函数，实际发送信号给目标进程。根据 `group` 参数的值，可以选择是否发送给整个进程组。

6. `unlock_task_sighand(p, &flags);`：解锁目标进程的信号处理数据结构。

7. 返回 `ret`，表示信号发送操作的结果。

这段代码的目标是向指定的进程发送信号，并且根据传递的参数决定是否将信号发送给整个进程组。它会尝试锁定目标进程的信号处理数据结构，然后调用 `send_signal` 函数来实际发送信号。发送完成后，它会解锁信号处理数据结构并返回信号发送的结果。

 ```c
static int send_signal(int sig, struct siginfo *info, struct task_struct *t,
			int group)
{
	int from_ancestor_ns = 0;

#ifdef CONFIG_PID_NS
	from_ancestor_ns = si_fromuser(info) &&
			   !task_pid_nr_ns(current, task_active_pid_ns(t));
#endif

	return __send_signal(sig, info, t, group, from_ancestor_ns);
}
 ```

  ```c

static int __send_signal(int sig, struct siginfo *info, struct task_struct *t,
			int group, int from_ancestor_ns)
{
	struct sigpending *pending;
	struct sigqueue *q;
	int override_rlimit;
	int ret = 0, result;

	assert_spin_locked(&t->sighand->siglock);

	result = TRACE_SIGNAL_IGNORED;
	if (!prepare_signal(sig, t,
			from_ancestor_ns || (info == SEND_SIG_FORCED)))
		goto ret;

	pending = group ? &t->signal->shared_pending : &t->pending;
	/*
	 * Short-circuit ignored signals and support queuing
	 * exactly one non-rt signal, so that we can get more
	 * detailed information about the cause of the signal.
	 */
	result = TRACE_SIGNAL_ALREADY_PENDING;
	if (legacy_queue(pending, sig))
		goto ret;

	result = TRACE_SIGNAL_DELIVERED;
	/*
	 * fast-pathed signals for kernel-internal things like SIGSTOP
	 * or SIGKILL.
	 */
	if (info == SEND_SIG_FORCED)
		goto out_set;

	/*
	 * Real-time signals must be queued if sent by sigqueue, or
	 * some other real-time mechanism.  It is implementation
	 * defined whether kill() does so.  We attempt to do so, on
	 * the principle of least surprise, but since kill is not
	 * allowed to fail with EAGAIN when low on memory we just
	 * make sure at least one signal gets delivered and don't
	 * pass on the info struct.
	 */
	if (sig < SIGRTMIN)
		override_rlimit = (is_si_special(info) || info->si_code >= 0);
	else
		override_rlimit = 0;

	q = __sigqueue_alloc(sig, t, GFP_ATOMIC | __GFP_NOTRACK_FALSE_POSITIVE,
		override_rlimit);
	if (q) {
		list_add_tail(&q->list, &pending->list);
		switch ((unsigned long) info) {
		case (unsigned long) SEND_SIG_NOINFO:
			q->info.si_signo = sig;
			q->info.si_errno = 0;
			q->info.si_code = SI_USER;
			q->info.si_pid = task_tgid_nr_ns(current,
							task_active_pid_ns(t));
			q->info.si_uid = from_kuid_munged(current_user_ns(), current_uid());
			break;
		case (unsigned long) SEND_SIG_PRIV:
			q->info.si_signo = sig;
			q->info.si_errno = 0;
			q->info.si_code = SI_KERNEL;
			q->info.si_pid = 0;
			q->info.si_uid = 0;
			break;
		default:
			copy_siginfo(&q->info, info);
			if (from_ancestor_ns)
				q->info.si_pid = 0;
			break;
		}

		userns_fixup_signal_uid(&q->info, t);

	} else if (!is_si_special(info)) {
		if (sig >= SIGRTMIN && info->si_code != SI_USER) {
			/*
			 * Queue overflow, abort.  We may abort if the
			 * signal was rt and sent by user using something
			 * other than kill().
			 */
			result = TRACE_SIGNAL_OVERFLOW_FAIL;
			ret = -EAGAIN;
			goto ret;
		} else {
			/*
			 * This is a silent loss of information.  We still
			 * send the signal, but the *info bits are lost.
			 */
			result = TRACE_SIGNAL_LOSE_INFO;
		}
	}

out_set:
	signalfd_notify(t, sig);
	sigaddset(&pending->signal, sig);
	complete_signal(sig, t, group);
ret:
	trace_signal_generate(sig, info, t, group, result);
	return ret;
}
 ```

这段代码实现了 `__send_signal` 函数，用于实际将信号发送给指定进程。这个函数是信号发送过程的核心部分：

1. `int __send_signal(int sig, struct siginfo *info, struct task_struct *t, int group, int from_ancestor_ns)`：这个函数用于实际将信号发送给指定进程。它接受信号编号 `sig`、信号信息结构体 `info`、目标进程结构体 `t`、发送方式 `group` 和一个整数 `from_ancestor_ns` 作为参数。

2. `assert_spin_locked(&t->sighand->siglock);`：确保当前进程已经获取了目标进程信号处理锁，以保证在信号发送过程中没有其他线程干扰。

3. `result = TRACE_SIGNAL_IGNORED;`：初始化结果变量为 `TRACE_SIGNAL_IGNORED`，表示最初状态下信号被忽略。

4. `if (!prepare_signal(sig, t, from_ancestor_ns || (info == SEND_SIG_FORCED)))`：如果无法准备发送信号。

   - 调用 `prepare_signal` 函数来检查是否可以发送信号。如果无法准备发送，跳转到 `ret` 处返回结果。

5. `pending = group ? &t->signal->shared_pending : &t->pending;`：根据 `group` 参数决定要使用的挂起信号列表，如果 `group` 为真，使用共享挂起信号列表，否则使用目标进程的挂起信号列表。

6. `if (legacy_queue(pending, sig))`：如果将信号添加到挂起信号列表中。

   - 调用 `legacy_queue` 函数，如果挂起信号列表中已经存在相同的信号，则表示该信号已经被挂起，跳转到 `ret` 处返回结果。

7. `if (info == SEND_SIG_FORCED)`：如果信号信息是 `SEND_SIG_FORCED`。

   - 直接跳转到 `out_set` 处，表示将信号添加到挂起信号列表中。

8. 检查信号是否为实时信号或普通信号，并设置是否覆盖资源限制的标志。

9. `q = __sigqueue_alloc(sig, t, GFP_ATOMIC | __GFP_NOTRACK_FALSE_POSITIVE, override_rlimit);`：调用 `__sigqueue_alloc` 函数分配一个信号队列节点，用于存储信号信息。

10. 如果成功分配了信号队列节点 `q`，则将其添加到相应的挂起信号列表中，并根据 `info` 的情况填充信号信息结构体 `q->info`。

11. 如果无法分配信号队列节点，判断是否为特殊信号，如果不是则处理队列溢出，如果是实时信号则返回失败。

12. 调用 `signalfd_notify` 函数，通知与目标进程关联的 `signalfd` 文件描述符。

13. 调用 `sigaddset` 函数，将信号添加到挂起信号集合中。

14. 调用 `complete_signal` 函数函数会调用signal_wake_up。这个函数会将线程的TIF_SIGPENDING标志设为1。这样后面就可以快速检测是否有未处理的信号了

15. 返回结果 `ret`，表示信号发送的结果。

16. 最后，调用 `trace_signal_generate` 函数，记录信号发送的跟踪事件，并返回结果 `ret`。

这段代码实现了实际的信号发送操作。它准备发送信号，判断是否需要加入挂起信号列表，处理特殊信号和实时信号，分配和填充信号信息结构体，通知 `signalfd` 文件描述符，添加信号到挂起信号集合，并最终完成信号发送的过程。

## 信号被线程处理
***当前进程陷入内核态，并准备返回用户态时处理信号***
现在，当前进程正在正常执行。刚才已经有进程发送信号，通过send_signal将信号存储在了当前进程的Pending queue当中。当前进程显然不会立刻处理这个信号。处理信号的时机，实际上是当前进程因为一些原因陷入内核态，然后返回用户态的时候。

现在，假设当前进程因为下面的原因进入内核态：
⚫中断
⚫系统调用
⚫异常
执行完内核态的操作之后，返回用户态。返回用户态内核内部将会使用这个函数：do_notify_resume函数：
```c
work_pending:
	tbnz	x1, #TIF_NEED_RESCHED, work_resched
	/* TIF_SIGPENDING, TIF_NOTIFY_RESUME or TIF_FOREIGN_FPSTATE case */
	ldr	x2, [sp, #S_PSTATE]
	mov	x0, sp				// 'regs'
	tst	x2, #PSR_MODE_MASK		// user mode regs?
	b.ne	no_work_pending			// returning to kernel
	enable_irq				// enable interrupts for do_notify_resume()
	bl	do_notify_resume
	b	ret_to_user
work_resched:
	bl	schedule

/*
 * "slow" syscall return path.
 */
ret_to_user:
	disable_irq				// disable interrupts
	ldr	x1, [tsk, #TI_FLAGS]
	and	x2, x1, #_TIF_WORK_MASK
	cbnz	x2, work_pending
	enable_step_tsk x1, x2
no_work_pending:
	kernel_exit 0, ret = 0
ENDPROC(ret_to_user)
```

```c
asmlinkage void do_notify_resume(struct pt_regs *regs,
                                 unsigned int thread_flags)
{
    // 如果线程标志中存在 _TIF_SIGPENDING 标志
    if (thread_flags & _TIF_SIGPENDING)
        // 调用 do_signal 函数来处理挂起的信号
        do_signal(regs);

    // 如果线程标志中存在 _TIF_NOTIFY_RESUME 标志
    if (thread_flags & _TIF_NOTIFY_RESUME) {
        // 清除线程标志中的 TIF_NOTIFY_RESUME 标志
        clear_thread_flag(TIF_NOTIFY_RESUME);
        // 调用 tracehook_notify_resume 函数来处理通知并恢复执行
        tracehook_notify_resume(regs);
    }

    // 如果线程标志中存在 _TIF_FOREIGN_FPSTATE 标志
    if (thread_flags & _TIF_FOREIGN_FPSTATE)
        // 恢复当前状态的浮点寄存器/向量寄存器状态
        fpsimd_restore_current_state();
}
```

```c
static void do_signal(struct pt_regs *regs)
{
	unsigned long continue_addr = 0, restart_addr = 0;
	int retval = 0;
	int syscall = (int)regs->syscallno;
	struct ksignal ksig;

	/*
	 * 如果之前是从系统调用返回，检查是否需要重新启动系统调用...
	 */
	if (syscall >= 0) {
		continue_addr = regs->pc;
		restart_addr = continue_addr - (compat_thumb_mode(regs) ? 2 : 4);
		retval = regs->regs[0];

		/*
		 * 避免通过 ret_to_user 陷入额外的系统调用重新启动。
		 */
		regs->syscallno = ~0UL;

		/*
		 * 为系统调用重新启动做准备。我们在这里这样做是为了调试器能够看到已经更改的 PC。
		 */
		switch (retval) {
		case -ERESTARTNOHAND:
		case -ERESTARTSYS:
		case -ERESTARTNOINTR:
		case -ERESTART_RESTARTBLOCK:
			regs->regs[0] = regs->orig_x0;
			regs->pc = restart_addr;
			break;
		}
	}

	/*
	 * 获取要传递的信号。在运行时使用 ptrace 时，此时调试器可能会更改我们的所有寄存器。
	 */
	if (get_signal(&ksig)) {
		/*
		 * 根据信号的设置，可能需要撤消重新启动系统调用的决定，但如果调试器已选择在不同的 PC 上重新启动，则跳过此步骤。
		 */
		if (regs->pc == restart_addr &&
		    (retval == -ERESTARTNOHAND ||
		     retval == -ERESTART_RESTARTBLOCK ||
		     (retval == -ERESTARTSYS &&
		      !(ksig.ka.sa.sa_flags & SA_RESTART)))) {
			regs->regs[0] = -EINTR;
			regs->pc = continue_addr;
		}

		handle_signal(&ksig, regs);
		return;
	}

	/*
	 * 处理重新启动不同的系统调用。与上述类似，如果调试器已选择在不同的 PC 上重新启动，则忽略重新启动。
	 */
	if (syscall >= 0 && regs->pc == restart_addr) {
		if (retval == -ERESTART_RESTARTBLOCK)
			setup_restart_syscall(regs);
		user_rewind_single_step(current);
	}

	restore_saved_sigmask();
}
```
可以看出，do_signal的核心是handle_signal

```c
static void handle_signal(struct ksignal *ksig, struct pt_regs *regs)
{
	struct task_struct *tsk = current;
	sigset_t *oldset = sigmask_to_save();
	int usig = ksig->sig;
	int ret;

	/*
	 * Set up the stack frame
	 */
	if (is_compat_task()) {
		if (ksig->ka.sa.sa_flags & SA_SIGINFO)
			ret = compat_setup_rt_frame(usig, ksig, oldset, regs);
		else
			ret = compat_setup_frame(usig, ksig, oldset, regs);
	} else {
		ret = setup_rt_frame(usig, ksig, oldset, regs);
	}

	/*
	 * Check that the resulting registers are actually sane.
	 */
	ret |= !valid_user_regs(&regs->user_regs);

	/*
	 * Fast forward the stepping logic so we step into the signal
	 * handler.
	 */
	if (!ret)
		user_fastforward_single_step(tsk);

	signal_setup_done(ret, ksig, 0);
}
```
这段代码实现了 `handle_signal` 函数，它负责在接收到信号时设置信号处理函数的栈帧并执行一些相关的处理：

1. `struct task_struct *tsk = current;`：获取当前正在运行的任务的指针，也就是当前进程的任务结构体。

2. `sigset_t *oldset = sigmask_to_save();`：获取当前进程的旧信号屏蔽集。

3. `int usig = ksig->sig;`：获取要处理的信号的编号。

4. `int ret;`：定义变量用于存储函数的返回值。

5. 设置栈帧：

   - 根据当前进程是否为兼容模式任务（32位应用程序在64位内核中运行），以及信号的设置情况，选择不同的栈帧设置函数。如果信号设置了 `SA_SIGINFO` 标志，调用对应的栈帧设置函数 `compat_setup_rt_frame`，否则调用 `compat_setup_frame`。
   - 如果当前进程不是兼容模式任务，调用 `setup_rt_frame` 来设置栈帧。

6. 检查生成的寄存器是否合理：

   - 检查之前设置的用户寄存器是否合理。如果栈帧设置函数返回非零，或者用户寄存器不合理，将 `ret` 的相应位设置为 1，表示出现问题。

7. 快速前进步进逻辑：

   - 如果之前的操作没有问题，调用 `user_fastforward_single_step` 函数，以便能够在信号处理函数中进行单步调试。

8. 完成信号设置：

   - 调用 `signal_setup_done` 函数，将栈帧设置的结果、信号信息和其他参数传递给它。这个函数会通知调度程序信号处理已经准备完成。

`handle_signal` 函数负责为信号处理函数设置栈帧，并根据情况执行相关处理，以确保信号的适当处理。这涉及了栈帧的设置、寄存器的检查、单步调试逻辑的前进，最终通知调度程序信号处理准备已完成，是通过setup_rt_frame来设定的。

```c
static int setup_rt_frame(int usig, struct ksignal *ksig, sigset_t *set,
                          struct pt_regs *regs)
{
    struct rt_sigframe __user *frame; // 声明一个指向用户空间的信号栈帧结构体指针
    int err = 0; // 初始化错误码变量

    frame = get_sigframe(ksig, regs); // 获取适合信号处理函数的用户空间栈帧
    if (!frame)
        return 1; // 如果获取失败，返回错误码 1 表示出现问题

    // 设置信号栈帧中的字段
    __put_user_error(0, &frame->uc.uc_flags, err); // 将值 0 存储到 uc_flags 字段
    __put_user_error(NULL, &frame->uc.uc_link, err); // 将 NULL 存储到 uc_link 字段

    // 保存备用堆栈信息
    err |= __save_altstack(&frame->uc.uc_stack, regs->sp);

    err |= setup_sigframe(frame, regs, set); // 设置信号栈帧的其他字段
    if (err == 0) {
        setup_return(regs, &ksig->ka, frame, usig); // 设置返回点，用于信号处理函数返回时
        if (ksig->ka.sa.sa_flags & SA_SIGINFO) {
            err |= copy_siginfo_to_user(&frame->info, &ksig->info); // 将信号信息复制到栈帧中
            regs->regs[1] = (unsigned long)&frame->info; // 设置寄存器中对应参数的值
            regs->regs[2] = (unsigned long)&frame->uc;
        }
    }

    return err; // 返回错误码，表示函数执行是否成功
}
```
先看get_sigframe函数
```c
static struct rt_sigframe __user *get_sigframe(struct ksignal *ksig,
                                               struct pt_regs *regs)
{
    unsigned long sp, sp_top;
    struct rt_sigframe __user *frame; // 声明一个指向用户空间信号栈帧结构体的指针

    sp = sp_top = sigsp(regs->sp, ksig); // 计算信号栈的起始地址

    sp = (sp - sizeof(struct rt_sigframe)) & ~15; // 根据信号栈帧的大小和对齐要求调整栈指针
    frame = (struct rt_sigframe __user *)sp; // 将栈指针指向调整后的位置，作为信号栈帧的起始地址

    /*
     * 检查我们是否可以实际写入信号栈帧。
     */
    if (!access_ok(VERIFY_WRITE, frame, sp_top - sp))
        frame = NULL; // 如果无法写入信号栈帧，将 frame 设为 NULL

    return frame; // 返回适合信号处理函数的用户空间栈帧指针
}
```
注意，这里的一堆操作就是将sig值给寄存器，ip寄存器设置成信号处理函数指针。具体的堆栈以及寄存器的配置还不是太懂后续研究。
处理完信号函数之后，进行一系列地恢复操作即可。首先恢复寄存器到陷入内核态之前的状态，然后恢复栈。这就是完整的信号生命周期
