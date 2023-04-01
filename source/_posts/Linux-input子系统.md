---
title: Linux input子系统
top: false
cover: false
toc: true
mathjax: true
date: 2022-01-01 21:12:46
password:
summary:
tags:
- linux
- input
categories:
- linux
keywords:
description:
---
<div>
<div>
<ul>
<li>
<blockquote>
<h5>Input driver ：主要实现对硬件设备的读写访问，中断设置，并把硬件产生的事件转换为核心层定义的规范提交给事件处理层。</h5>
</blockquote>
</li>
<li>
<blockquote>
<h5>Input core ：承上启下。为设备驱动层提供了规范和接口；通知事件处理层对事件进行处理；</h5>
</blockquote>
</li>
<li>
<blockquote>
<h5>Event handler ：提供用户编程的接口（设备节点），并处理驱动层提交的数据处理。</h5>
</blockquote>
</li>
</ul>
<p><img src="Linux-input子系统/2909691-20220819093409715-1604400596.png" alt="" /></p>
<h1>1输入子系统框架分析</h1>
<div>
<div>
<h2>1.1设备驱动层（Input driver）</h2>
<ul>
<li>device是纯硬件操作层，包含不同的硬件接口处理，如gpio等</li>
<li>对于每种不同的具体硬件操作，都对应着不同的input_dev结构体</li>
<li>该结构体内部也包含着一个h_list，指向handle</li>
</ul>
</div>
</div>
<div>
<div>
<div>
<div>
<h2>1.2.系统核心层（Input core）</h2>
<ul>
<li>申请主设备号;</li>
<li>提供input_register_device跟input_register_handler函数分别用于注册device跟handler;</li>
<li>提供input_register_handle函数用于注册一个事件处理，代表一个成功配对的input_dev和input_handler;</li>
</ul>
</div>
</div>
<h2>1.3.事件处理层（Event handler）</h2>
<ul>
<li>不涉及硬件方面的具体操作，handler层是纯软件层，包含不同的解决方案，如键盘，鼠标，游戏手柄等；</li>
<li>对于不同的解决方案，都包含一个名为input_handler的结构体，该结构体内含的主要成员如下：</li>
</ul>
<table>
<thead>
<tr><th>成员</th><th>功能</th></tr>
</thead>
<tbody>
<tr>
<td>.id_table</td>
<td>一个存放该handler所支持的设备id的表（其实内部存放的是EV_xxx事件,用于判断device是否支持该事件）</td>
</tr>
<tr>
<td>.fops</td>
<td>该handler的file_operation</td>
</tr>
<tr>
<td>.connect</td>
<td>连接该handler跟所支持device的函数</td>
</tr>
<tr>
<td>.disconnect</td>
<td>断开该连接</td>
</tr>
<tr>
<td>.event</td>
<td>事件处理函数，让device调用</td>
</tr>
<tr>
<td>h_list</td>
<td>是一个链表，该链表保存着该handler到所支持的所有device的中间站：handle结构体的指针</td>
</tr>
</tbody>
</table>
</div>
<h1>2.两条链表连接dev和handler</h1>
<div class="cnblogs_code">
<pre>#file pwd: drivers/input/input.c<br /><br />MODULE_AUTHOR(<span style="color: #800000;">"</span><span style="color: #800000;">Vojtech Pavlik &lt;vojtech@suse.cz&gt;</span><span style="color: #800000;">"</span><span style="color: #000000;">);
MODULE_DESCRIPTION(</span><span style="color: #800000;">"</span><span style="color: #800000;">Input core</span><span style="color: #800000;">"</span><span style="color: #000000;">);
MODULE_LICENSE(</span><span style="color: #800000;">"</span><span style="color: #800000;">GPL</span><span style="color: #800000;">"</span><span style="color: #000000;">);

</span><span style="color: #0000ff;">#define</span> INPUT_MAX_CHAR_DEVICES        1024
<span style="color: #0000ff;">#define</span> INPUT_FIRST_DYNAMIC_DEV        256
<span style="color: #0000ff;">static</span><span style="color: #000000;"> DEFINE_IDA(input_ida);

</span><span style="color: #0000ff;">static</span><span style="color: #000000;"> LIST_HEAD(input_dev_list);
</span><span style="color: #0000ff;">static</span> LIST_HEAD(input_handler_list);</pre>
</div>
在input.c文件中两个全局链表input_handler_list和<span style="color: #000000;">input_dev_list</span>，通过handle相互关联：</div>
<div><img src="Linux-input子系统/2909691-20220819094250974-180404869.webp" alt="" />
<p>&nbsp;</p>
<h1>3.输入子系统代码分析</h1>
<p>文件路径：driver/input/input.c （核心层）</p>
<div class="cnblogs_code">
<pre><span style="color: #008080;"> 1</span> <span style="color: #0000ff;">static</span> <span style="color: #0000ff;">int</span> __init input_init(<span style="color: #0000ff;">void</span><span style="color: #000000;">)
</span><span style="color: #008080;"> 2</span> <span style="color: #000000;">{
</span><span style="color: #008080;"> 3</span>     <span style="color: #0000ff;">int</span><span style="color: #000000;"> err;
</span><span style="color: #008080;"> 4</span> 
<span style="color: #008080;"> 5</span>     err = class_register(&amp;<span style="color: #000000;">input_class);  <code class="  language-cpp"><span class="token comment">//在/sys/class下创建逻辑（input）类，在类下面挂载input设备</span></code>
</span><span style="color: #008080;"> 6</span>     <span style="color: #0000ff;">if</span><span style="color: #000000;"> (err) {
</span><span style="color: #008080;"> 7</span>         pr_err(<span style="color: #800000;">"</span><span style="color: #800000;">unable to register input_dev class\n</span><span style="color: #800000;">"</span><span style="color: #000000;">);
</span><span style="color: #008080;"> 8</span>         <span style="color: #0000ff;">return</span><span style="color: #000000;"> err;
</span><span style="color: #008080;"> 9</span> <span style="color: #000000;">    }
</span><span style="color: #008080;">10</span> 
<span style="color: #008080;">11</span>     err =<span style="color: #000000;"> input_proc_init();　　<code class="  language-cpp"><span class="token punctuation"><span class="token comment">//在/proc下面建立相关的虚拟文件，proc下创建的文件可以看作是虚拟文件对内核读写的一种操作</span></span></code>
</span><span style="color: #008080;">12</span>     <span style="color: #0000ff;">if</span><span style="color: #000000;"> (err)
</span><span style="color: #008080;">13</span>         <span style="color: #0000ff;">goto</span><span style="color: #000000;"> fail1;
</span><span style="color: #008080;">14</span> 
<span style="color: #008080;">15</span>     err = register_chrdev_region(MKDEV(INPUT_MAJOR, <span style="color: #800080;">0</span><span style="color: #000000;">),//在/dev下创建input设备号
</span><span style="color: #008080;">16</span>                      INPUT_MAX_CHAR_DEVICES, <span style="color: #800000;">"</span><span style="color: #800000;">input</span><span style="color: #800000;">"</span><span style="color: #000000;">);
</span><span style="color: #008080;">17</span>     <span style="color: #0000ff;">if</span><span style="color: #000000;"> (err) {
</span><span style="color: #008080;">18</span>         pr_err(<span style="color: #800000;">"</span><span style="color: #800000;">unable to register char major %d</span><span style="color: #800000;">"</span><span style="color: #000000;">, INPUT_MAJOR);
</span><span style="color: #008080;">19</span>         <span style="color: #0000ff;">goto</span><span style="color: #000000;"> fail2;
</span><span style="color: #008080;">20</span> <span style="color: #000000;">    }
</span><span style="color: #008080;">21</span> 
<span style="color: #008080;">22</span>     <span style="color: #0000ff;">return</span> <span style="color: #800080;">0</span><span style="color: #000000;">;
</span><span style="color: #008080;">23</span> 
<span style="color: #008080;">24</span> <span style="color: #000000;"> fail2:    input_proc_exit();
</span><span style="color: #008080;">25</span>  fail1:    class_unregister(&amp;<span style="color: #000000;">input_class);
</span><span style="color: #008080;">26</span>     <span style="color: #0000ff;">return</span><span style="color: #000000;"> err;
</span><span style="color: #008080;">27</span> <span style="color: #000000;">}
</span><span style="color: #008080;">28</span> 
<span style="color: #008080;">29</span> <span style="color: #0000ff;">static</span> <span style="color: #0000ff;">void</span> __exit input_exit(<span style="color: #0000ff;">void</span><span style="color: #000000;">)
</span><span style="color: #008080;">30</span> <span style="color: #000000;">{
</span><span style="color: #008080;">31</span> <span style="color: #000000;">    input_proc_exit();
</span><span style="color: #008080;">32</span>     unregister_chrdev_region(MKDEV(INPUT_MAJOR, <span style="color: #800080;">0</span><span style="color: #000000;">),
</span><span style="color: #008080;">33</span> <span style="color: #000000;">                 INPUT_MAX_CHAR_DEVICES);
</span><span style="color: #008080;">34</span>     class_unregister(&amp;<span style="color: #000000;">input_class);
</span><span style="color: #008080;">35</span> <span style="color: #000000;">}
</span><span style="color: #008080;">36</span> 
<span style="color: #008080;">37</span> <span style="color: #000000;">subsys_initcall(input_init);
</span><span style="color: #008080;">38</span> module_exit(input_exit);</pre>
</div>
<p>现在基本框架已经建成，如何往input系统里面注册dev和hanlder呢？</p>
<h2>3.1注册dev</h2>
<div class="cnblogs_code">
<pre><span style="color: #008080;">  1</span> <span style="color: #008000;">/*</span><span style="color: #008000;">*
</span><span style="color: #008080;">  2</span> <span style="color: #008000;"> * struct input_dev - represents an input device
</span><span style="color: #008080;">  3</span> <span style="color: #008000;"> * @name: name of the device
</span><span style="color: #008080;">  4</span> <span style="color: #008000;"> * @phys: physical path to the device in the system hierarchy
</span><span style="color: #008080;">  5</span> <span style="color: #008000;"> * @uniq: unique identification code for the device (if device has it)
</span><span style="color: #008080;">  6</span> <span style="color: #008000;"> * @id: id of the device (struct input_id)
</span><span style="color: #008080;">  7</span> <span style="color: #008000;"> * @propbit: bitmap of device properties and quirks
</span><span style="color: #008080;">  8</span> <span style="color: #008000;"> * @evbit: bitmap of types of events supported by the device (EV_KEY,
</span><span style="color: #008080;">  9</span> <span style="color: #008000;"> *    EV_REL, etc.)
</span><span style="color: #008080;"> 10</span> <span style="color: #008000;"> * @keybit: bitmap of keys/buttons this device has
</span><span style="color: #008080;"> 11</span> <span style="color: #008000;"> * @relbit: bitmap of relative axes for the device
</span><span style="color: #008080;"> 12</span> <span style="color: #008000;"> * @absbit: bitmap of absolute axes for the device
</span><span style="color: #008080;"> 13</span> <span style="color: #008000;"> * @mscbit: bitmap of miscellaneous events supported by the device
</span><span style="color: #008080;"> 14</span> <span style="color: #008000;"> * @ledbit: bitmap of leds present on the device
</span><span style="color: #008080;"> 15</span> <span style="color: #008000;"> * @sndbit: bitmap of sound effects supported by the device
</span><span style="color: #008080;"> 16</span> <span style="color: #008000;"> * @ffbit: bitmap of force feedback effects supported by the device
</span><span style="color: #008080;"> 17</span> <span style="color: #008000;"> * @swbit: bitmap of switches present on the device
</span><span style="color: #008080;"> 18</span> <span style="color: #008000;"> * @hint_events_per_packet: average number of events generated by the
</span><span style="color: #008080;"> 19</span> <span style="color: #008000;"> *    device in a packet (between EV_SYN/SYN_REPORT events). Used by
</span><span style="color: #008080;"> 20</span> <span style="color: #008000;"> *    event handlers to estimate size of the buffer needed to hold
</span><span style="color: #008080;"> 21</span> <span style="color: #008000;"> *    events.
</span><span style="color: #008080;"> 22</span> <span style="color: #008000;"> * @keycodemax: size of keycode table
</span><span style="color: #008080;"> 23</span> <span style="color: #008000;"> * @keycodesize: size of elements in keycode table
</span><span style="color: #008080;"> 24</span> <span style="color: #008000;"> * @keycode: map of scancodes to keycodes for this device
</span><span style="color: #008080;"> 25</span> <span style="color: #008000;"> * @getkeycode: optional legacy method to retrieve current keymap.
</span><span style="color: #008080;"> 26</span> <span style="color: #008000;"> * @setkeycode: optional method to alter current keymap, used to implement
</span><span style="color: #008080;"> 27</span> <span style="color: #008000;"> *    sparse keymaps. If not supplied default mechanism will be used.
</span><span style="color: #008080;"> 28</span> <span style="color: #008000;"> *    The method is being called while holding event_lock and thus must
</span><span style="color: #008080;"> 29</span> <span style="color: #008000;"> *    not sleep
</span><span style="color: #008080;"> 30</span> <span style="color: #008000;"> * @ff: force feedback structure associated with the device if device
</span><span style="color: #008080;"> 31</span> <span style="color: #008000;"> *    supports force feedback effects
</span><span style="color: #008080;"> 32</span> <span style="color: #008000;"> * @repeat_key: stores key code of the last key pressed; used to implement
</span><span style="color: #008080;"> 33</span> <span style="color: #008000;"> *    software autorepeat
</span><span style="color: #008080;"> 34</span> <span style="color: #008000;"> * @timer: timer for software autorepeat
</span><span style="color: #008080;"> 35</span> <span style="color: #008000;"> * @rep: current values for autorepeat parameters (delay, rate)
</span><span style="color: #008080;"> 36</span> <span style="color: #008000;"> * @mt: pointer to multitouch state
</span><span style="color: #008080;"> 37</span> <span style="color: #008000;"> * @absinfo: array of &amp;struct input_absinfo elements holding information
</span><span style="color: #008080;"> 38</span> <span style="color: #008000;"> *    about absolute axes (current value, min, max, flat, fuzz,
</span><span style="color: #008080;"> 39</span> <span style="color: #008000;"> *    resolution)
</span><span style="color: #008080;"> 40</span> <span style="color: #008000;"> * @key: reflects current state of device's keys/buttons
</span><span style="color: #008080;"> 41</span> <span style="color: #008000;"> * @led: reflects current state of device's LEDs
</span><span style="color: #008080;"> 42</span> <span style="color: #008000;"> * @snd: reflects current state of sound effects
</span><span style="color: #008080;"> 43</span> <span style="color: #008000;"> * @sw: reflects current state of device's switches
</span><span style="color: #008080;"> 44</span> <span style="color: #008000;"> * @open: this method is called when the very first user calls
</span><span style="color: #008080;"> 45</span> <span style="color: #008000;"> *    input_open_device(). The driver must prepare the device
</span><span style="color: #008080;"> 46</span> <span style="color: #008000;"> *    to start generating events (start polling thread,
</span><span style="color: #008080;"> 47</span> <span style="color: #008000;"> *    request an IRQ, submit URB, etc.)
</span><span style="color: #008080;"> 48</span> <span style="color: #008000;"> * @close: this method is called when the very last user calls
</span><span style="color: #008080;"> 49</span> <span style="color: #008000;"> *    input_close_device().
</span><span style="color: #008080;"> 50</span> <span style="color: #008000;"> * @flush: purges the device. Most commonly used to get rid of force
</span><span style="color: #008080;"> 51</span> <span style="color: #008000;"> *    feedback effects loaded into the device when disconnecting
</span><span style="color: #008080;"> 52</span> <span style="color: #008000;"> *    from it
</span><span style="color: #008080;"> 53</span> <span style="color: #008000;"> * @event: event handler for events sent _to_ the device, like EV_LED
</span><span style="color: #008080;"> 54</span> <span style="color: #008000;"> *    or EV_SND. The device is expected to carry out the requested
</span><span style="color: #008080;"> 55</span> <span style="color: #008000;"> *    action (turn on a LED, play sound, etc.) The call is protected
</span><span style="color: #008080;"> 56</span> <span style="color: #008000;"> *    by @event_lock and must not sleep
</span><span style="color: #008080;"> 57</span> <span style="color: #008000;"> * @grab: input handle that currently has the device grabbed (via
</span><span style="color: #008080;"> 58</span> <span style="color: #008000;"> *    EVIOCGRAB ioctl). When a handle grabs a device it becomes sole
</span><span style="color: #008080;"> 59</span> <span style="color: #008000;"> *    recipient for all input events coming from the device
</span><span style="color: #008080;"> 60</span> <span style="color: #008000;"> * @event_lock: this spinlock is is taken when input core receives
</span><span style="color: #008080;"> 61</span> <span style="color: #008000;"> *    and processes a new event for the device (in input_event()).
</span><span style="color: #008080;"> 62</span> <span style="color: #008000;"> *    Code that accesses and/or modifies parameters of a device
</span><span style="color: #008080;"> 63</span> <span style="color: #008000;"> *    (such as keymap or absmin, absmax, absfuzz, etc.) after device
</span><span style="color: #008080;"> 64</span> <span style="color: #008000;"> *    has been registered with input core must take this lock.
</span><span style="color: #008080;"> 65</span> <span style="color: #008000;"> * @mutex: serializes calls to open(), close() and flush() methods
</span><span style="color: #008080;"> 66</span> <span style="color: #008000;"> * @users: stores number of users (input handlers) that opened this
</span><span style="color: #008080;"> 67</span> <span style="color: #008000;"> *    device. It is used by input_open_device() and input_close_device()
</span><span style="color: #008080;"> 68</span> <span style="color: #008000;"> *    to make sure that dev-&gt;open() is only called when the first
</span><span style="color: #008080;"> 69</span> <span style="color: #008000;"> *    user opens device and dev-&gt;close() is called when the very
</span><span style="color: #008080;"> 70</span> <span style="color: #008000;"> *    last user closes the device
</span><span style="color: #008080;"> 71</span> <span style="color: #008000;"> * @going_away: marks devices that are in a middle of unregistering and
</span><span style="color: #008080;"> 72</span> <span style="color: #008000;"> *    causes input_open_device*() fail with -ENODEV.
</span><span style="color: #008080;"> 73</span> <span style="color: #008000;"> * @dev: driver model's view of this device
</span><span style="color: #008080;"> 74</span> <span style="color: #008000;"> * @h_list: list of input handles associated with the device. When
</span><span style="color: #008080;"> 75</span> <span style="color: #008000;"> *    accessing the list dev-&gt;mutex must be held
</span><span style="color: #008080;"> 76</span> <span style="color: #008000;"> * @node: used to place the device onto input_dev_list
</span><span style="color: #008080;"> 77</span> <span style="color: #008000;"> * @num_vals: number of values queued in the current frame
</span><span style="color: #008080;"> 78</span> <span style="color: #008000;"> * @max_vals: maximum number of values queued in a frame
</span><span style="color: #008080;"> 79</span> <span style="color: #008000;"> * @vals: array of values queued in the current frame
</span><span style="color: #008080;"> 80</span> <span style="color: #008000;"> * @devres_managed: indicates that devices is managed with devres framework
</span><span style="color: #008080;"> 81</span> <span style="color: #008000;"> *    and needs not be explicitly unregistered or freed.
</span><span style="color: #008080;"> 82</span>  <span style="color: #008000;">*/</span>
<span style="color: #008080;"> 83</span> <span style="color: #0000ff;">struct</span><span style="color: #000000;"> input_dev {
</span><span style="color: #008080;"> 84</span>     <span style="color: #0000ff;">const</span> <span style="color: #0000ff;">char</span> *<span style="color: #000000;">name;
</span><span style="color: #008080;"> 85</span>     <span style="color: #0000ff;">const</span> <span style="color: #0000ff;">char</span> *<span style="color: #000000;">phys;
</span><span style="color: #008080;"> 86</span>     <span style="color: #0000ff;">const</span> <span style="color: #0000ff;">char</span> *<span style="color: #000000;">uniq;
</span><span style="color: #008080;"> 87</span>     <span style="color: #0000ff;">struct</span><span style="color: #000000;"> input_id id;
</span><span style="color: #008080;"> 88</span> 
<span style="color: #008080;"> 89</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> propbit[BITS_TO_LONGS(INPUT_PROP_CNT)];
</span><span style="color: #008080;"> 90</span> 
<span style="color: #008080;"> 91</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> evbit[BITS_TO_LONGS(EV_CNT)];
</span><span style="color: #008080;"> 92</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> keybit[BITS_TO_LONGS(KEY_CNT)];
</span><span style="color: #008080;"> 93</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> relbit[BITS_TO_LONGS(REL_CNT)];
</span><span style="color: #008080;"> 94</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> absbit[BITS_TO_LONGS(ABS_CNT)];
</span><span style="color: #008080;"> 95</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> mscbit[BITS_TO_LONGS(MSC_CNT)];
</span><span style="color: #008080;"> 96</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> ledbit[BITS_TO_LONGS(LED_CNT)];
</span><span style="color: #008080;"> 97</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> sndbit[BITS_TO_LONGS(SND_CNT)];
</span><span style="color: #008080;"> 98</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> ffbit[BITS_TO_LONGS(FF_CNT)];
</span><span style="color: #008080;"> 99</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> swbit[BITS_TO_LONGS(SW_CNT)];
</span><span style="color: #008080;">100</span> 
<span style="color: #008080;">101</span>     unsigned <span style="color: #0000ff;">int</span><span style="color: #000000;"> hint_events_per_packet;
</span><span style="color: #008080;">102</span> 
<span style="color: #008080;">103</span>     unsigned <span style="color: #0000ff;">int</span><span style="color: #000000;"> keycodemax;
</span><span style="color: #008080;">104</span>     unsigned <span style="color: #0000ff;">int</span><span style="color: #000000;"> keycodesize;
</span><span style="color: #008080;">105</span>     <span style="color: #0000ff;">void</span> *<span style="color: #000000;">keycode;
</span><span style="color: #008080;">106</span> 
<span style="color: #008080;">107</span>     <span style="color: #0000ff;">int</span> (*setkeycode)(<span style="color: #0000ff;">struct</span> input_dev *<span style="color: #000000;">dev,
</span><span style="color: #008080;">108</span>               <span style="color: #0000ff;">const</span> <span style="color: #0000ff;">struct</span> input_keymap_entry *<span style="color: #000000;">ke,
</span><span style="color: #008080;">109</span>               unsigned <span style="color: #0000ff;">int</span> *<span style="color: #000000;">old_keycode);
</span><span style="color: #008080;">110</span>     <span style="color: #0000ff;">int</span> (*getkeycode)(<span style="color: #0000ff;">struct</span> input_dev *<span style="color: #000000;">dev,
</span><span style="color: #008080;">111</span>               <span style="color: #0000ff;">struct</span> input_keymap_entry *<span style="color: #000000;">ke);
</span><span style="color: #008080;">112</span> 
<span style="color: #008080;">113</span>     <span style="color: #0000ff;">struct</span> ff_device *<span style="color: #000000;">ff;
</span><span style="color: #008080;">114</span> 
<span style="color: #008080;">115</span>     unsigned <span style="color: #0000ff;">int</span><span style="color: #000000;"> repeat_key;
</span><span style="color: #008080;">116</span>     <span style="color: #0000ff;">struct</span><span style="color: #000000;"> timer_list timer;
</span><span style="color: #008080;">117</span> 
<span style="color: #008080;">118</span>     <span style="color: #0000ff;">int</span><span style="color: #000000;"> rep[REP_CNT];
</span><span style="color: #008080;">119</span> 
<span style="color: #008080;">120</span>     <span style="color: #0000ff;">struct</span> input_mt *<span style="color: #000000;">mt;
</span><span style="color: #008080;">121</span> 
<span style="color: #008080;">122</span>     <span style="color: #0000ff;">struct</span> input_absinfo *<span style="color: #000000;">absinfo;
</span><span style="color: #008080;">123</span> 
<span style="color: #008080;">124</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> key[BITS_TO_LONGS(KEY_CNT)];
</span><span style="color: #008080;">125</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> led[BITS_TO_LONGS(LED_CNT)];
</span><span style="color: #008080;">126</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> snd[BITS_TO_LONGS(SND_CNT)];
</span><span style="color: #008080;">127</span>     unsigned <span style="color: #0000ff;">long</span><span style="color: #000000;"> sw[BITS_TO_LONGS(SW_CNT)];
</span><span style="color: #008080;">128</span> 
<span style="color: #008080;">129</span>     <span style="color: #0000ff;">int</span> (*open)(<span style="color: #0000ff;">struct</span> input_dev *<span style="color: #000000;">dev);
</span><span style="color: #008080;">130</span>     <span style="color: #0000ff;">void</span> (*close)(<span style="color: #0000ff;">struct</span> input_dev *<span style="color: #000000;">dev);
</span><span style="color: #008080;">131</span>     <span style="color: #0000ff;">int</span> (*flush)(<span style="color: #0000ff;">struct</span> input_dev *dev, <span style="color: #0000ff;">struct</span> file *<span style="color: #000000;">file);
</span><span style="color: #008080;">132</span>     <span style="color: #0000ff;">int</span> (*<span style="color: #0000ff;">event</span>)(<span style="color: #0000ff;">struct</span> input_dev *dev, unsigned <span style="color: #0000ff;">int</span> type, unsigned <span style="color: #0000ff;">int</span> code, <span style="color: #0000ff;">int</span><span style="color: #000000;"> value);
</span><span style="color: #008080;">133</span> 
<span style="color: #008080;">134</span>     <span style="color: #0000ff;">struct</span> input_handle __rcu *<span style="color: #000000;">grab;
</span><span style="color: #008080;">135</span> 
<span style="color: #008080;">136</span> <span style="color: #000000;">    spinlock_t event_lock;
</span><span style="color: #008080;">137</span>     <span style="color: #0000ff;">struct</span><span style="color: #000000;"> mutex mutex;
</span><span style="color: #008080;">138</span> 
<span style="color: #008080;">139</span>     unsigned <span style="color: #0000ff;">int</span><span style="color: #000000;"> users;
</span><span style="color: #008080;">140</span>     <span style="color: #0000ff;">bool</span><span style="color: #000000;"> going_away;
</span><span style="color: #008080;">141</span> 
<span style="color: #008080;">142</span>     <span style="color: #0000ff;">struct</span><span style="color: #000000;"> device dev;
</span><span style="color: #008080;">143</span> 
<span style="color: #008080;">144</span>     <span style="color: #0000ff;">struct</span><span style="color: #000000;"> list_head    h_list;
</span><span style="color: #008080;">145</span>     <span style="color: #0000ff;">struct</span><span style="color: #000000;"> list_head    node;
</span><span style="color: #008080;">146</span> 
<span style="color: #008080;">147</span>     unsigned <span style="color: #0000ff;">int</span><span style="color: #000000;"> num_vals;
</span><span style="color: #008080;">148</span>     unsigned <span style="color: #0000ff;">int</span><span style="color: #000000;"> max_vals;
</span><span style="color: #008080;">149</span>     <span style="color: #0000ff;">struct</span> input_value *<span style="color: #000000;">vals;
</span><span style="color: #008080;">150</span> 
<span style="color: #008080;">151</span>     <span style="color: #0000ff;">bool</span><span style="color: #000000;"> devres_managed;
</span><span style="color: #008080;">152</span> <span style="color: #000000;">};
</span><span style="color: #008080;">153</span> <span style="color: #0000ff;">#define</span> to_input_dev(d) container_of(d, struct input_dev, dev)</pre>
</div>
<p>&nbsp;</p>
<div>
<div>&nbsp;</div>
<div class="cnblogs_code">
<pre><span style="color: #008080;">  1</span> <span style="color: #008000;">/*</span><span style="color: #008000;">*
</span><span style="color: #008080;">  2</span> <span style="color: #008000;"> * input_register_device - register device with input core
</span><span style="color: #008080;">  3</span> <span style="color: #008000;"> * @dev: device to be registered
</span><span style="color: #008080;">  4</span> <span style="color: #008000;"> *
</span><span style="color: #008080;">  5</span> <span style="color: #008000;"> * This function registers device with input core. The device must be
</span><span style="color: #008080;">  6</span> <span style="color: #008000;"> * allocated with input_allocate_device() and all it's capabilities
</span><span style="color: #008080;">  7</span> <span style="color: #008000;"> * set up before registering.
</span><span style="color: #008080;">  8</span> <span style="color: #008000;"> * If function fails the device must be freed with input_free_device().
</span><span style="color: #008080;">  9</span> <span style="color: #008000;"> * Once device has been successfully registered it can be unregistered
</span><span style="color: #008080;"> 10</span> <span style="color: #008000;"> * with input_unregister_device(); input_free_device() should not be
</span><span style="color: #008080;"> 11</span> <span style="color: #008000;"> * called in this case.
</span><span style="color: #008080;"> 12</span> <span style="color: #008000;"> *
</span><span style="color: #008080;"> 13</span> <span style="color: #008000;"> * Note that this function is also used to register managed input devices
</span><span style="color: #008080;"> 14</span> <span style="color: #008000;"> * (ones allocated with devm_input_allocate_device()). Such managed input
</span><span style="color: #008080;"> 15</span> <span style="color: #008000;"> * devices need not be explicitly unregistered or freed, their tear down
</span><span style="color: #008080;"> 16</span> <span style="color: #008000;"> * is controlled by the devres infrastructure. It is also worth noting
</span><span style="color: #008080;"> 17</span> <span style="color: #008000;"> * that tear down of managed input devices is internally a 2-step process:
</span><span style="color: #008080;"> 18</span> <span style="color: #008000;"> * registered managed input device is first unregistered, but stays in
</span><span style="color: #008080;"> 19</span> <span style="color: #008000;"> * memory and can still handle input_event() calls (although events will
</span><span style="color: #008080;"> 20</span> <span style="color: #008000;"> * not be delivered anywhere). The freeing of managed input device will
</span><span style="color: #008080;"> 21</span> <span style="color: #008000;"> * happen later, when devres stack is unwound to the point where device
</span><span style="color: #008080;"> 22</span> <span style="color: #008000;"> * allocation was made.
</span><span style="color: #008080;"> 23</span>  <span style="color: #008000;">*/</span>
<span style="color: #008080;"> 24</span> <span style="color: #0000ff;">int</span> input_register_device(<span style="color: #0000ff;">struct</span> input_dev *<span style="color: #000000;">dev)
</span><span style="color: #008080;"> 25</span> <span style="color: #000000;">{
</span><span style="color: #008080;"> 26</span>     <span style="color: #0000ff;">struct</span> input_devres *devres =<span style="color: #000000;"> NULL;
</span><span style="color: #008080;"> 27</span>      <span style="color: #008000;">/*</span><span style="color: #008000;"> 输入事件的处理接口指针，用于和设备的事件类型进行匹配 </span><span style="color: #008000;">*/</span>  
<span style="color: #008080;"> 28</span>     <span style="color: #0000ff;">struct</span> input_handler *<span style="color: #000000;">handler;
</span><span style="color: #008080;"> 29</span>     unsigned <span style="color: #0000ff;">int</span><span style="color: #000000;"> packet_size;
</span><span style="color: #008080;"> 30</span>     <span style="color: #0000ff;">const</span> <span style="color: #0000ff;">char</span> *<span style="color: #000000;">path;
</span><span style="color: #008080;"> 31</span>     <span style="color: #0000ff;">int</span><span style="color: #000000;"> error;
</span><span style="color: #008080;"> 32</span> 
<span style="color: #008080;"> 33</span>     <span style="color: #0000ff;">if</span> (dev-&gt;<span style="color: #000000;">devres_managed) {
</span><span style="color: #008080;"> 34</span>         devres =<span style="color: #000000;"> devres_alloc(devm_input_device_unregister,
</span><span style="color: #008080;"> 35</span>                       <span style="color: #0000ff;">sizeof</span>(<span style="color: #0000ff;">struct</span><span style="color: #000000;"> input_devres), GFP_KERNEL);
</span><span style="color: #008080;"> 36</span>         <span style="color: #0000ff;">if</span> (!<span style="color: #000000;">devres)
</span><span style="color: #008080;"> 37</span>             <span style="color: #0000ff;">return</span> -<span style="color: #000000;">ENOMEM;
</span><span style="color: #008080;"> 38</span> 
<span style="color: #008080;"> 39</span>         devres-&gt;input =<span style="color: #000000;"> dev;
</span><span style="color: #008080;"> 40</span> <span style="color: #000000;">    }
</span><span style="color: #008080;"> 41</span> 
<span style="color: #008080;"> 42</span>     <span style="color: #008000;">/*</span><span style="color: #008000;"> Every input device generates EV_SYN/SYN_REPORT events. </span><span style="color: #008000;">*/</span>
<span style="color: #008080;"> 43</span>     __set_bit(EV_SYN, dev-&gt;<span style="color: #000000;">evbit);
</span><span style="color: #008080;"> 44</span> 
<span style="color: #008080;"> 45</span>     <span style="color: #008000;">/*</span><span style="color: #008000;"> KEY_RESERVED is not supposed to be transmitted to userspace. </span><span style="color: #008000;">*/</span>
<span style="color: #008080;"> 46</span>     __clear_bit(KEY_RESERVED, dev-&gt;<span style="color: #000000;">keybit);
</span><span style="color: #008080;"> 47</span> 
<span style="color: #008080;"> 48</span>     <span style="color: #008000;">/*</span><span style="color: #008000;"> Make sure that bitmasks not mentioned in dev-&gt;evbit are clean. </span><span style="color: #008000;">*/</span>
<span style="color: #008080;"> 49</span> <span style="color: #000000;">    input_cleanse_bitmasks(dev);
</span><span style="color: #008080;"> 50</span> 
<span style="color: #008080;"> 51</span>     packet_size =<span style="color: #000000;"> input_estimate_events_per_packet(dev);
</span><span style="color: #008080;"> 52</span>     <span style="color: #0000ff;">if</span> (dev-&gt;hint_events_per_packet &lt;<span style="color: #000000;"> packet_size)
</span><span style="color: #008080;"> 53</span>         dev-&gt;hint_events_per_packet =<span style="color: #000000;"> packet_size;
</span><span style="color: #008080;"> 54</span> 
<span style="color: #008080;"> 55</span>     dev-&gt;max_vals = dev-&gt;hint_events_per_packet + <span style="color: #800080;">2</span><span style="color: #000000;">;
</span><span style="color: #008080;"> 56</span>     dev-&gt;vals = kcalloc(dev-&gt;max_vals, <span style="color: #0000ff;">sizeof</span>(*dev-&gt;<span style="color: #000000;">vals), GFP_KERNEL);
</span><span style="color: #008080;"> 57</span>     <span style="color: #0000ff;">if</span> (!dev-&gt;<span style="color: #000000;">vals) {
</span><span style="color: #008080;"> 58</span>         error = -<span style="color: #000000;">ENOMEM;
</span><span style="color: #008080;"> 59</span>         <span style="color: #0000ff;">goto</span><span style="color: #000000;"> err_devres_free;
</span><span style="color: #008080;"> 60</span> <span style="color: #000000;">    }
</span><span style="color: #008080;"> 61</span> 
<span style="color: #008080;"> 62</span>     <span style="color: #008000;">/*</span>
<span style="color: #008080;"> 63</span> <span style="color: #008000;">     * If delay and period are pre-set by the driver, then autorepeating
</span><span style="color: #008080;"> 64</span> <span style="color: #008000;">     * is handled by the driver itself and we don't do it in input.c.
</span><span style="color: #008080;"> 65</span>      <span style="color: #008000;">*/</span>
<span style="color: #008080;"> 66</span>     <span style="color: #0000ff;">if</span> (!dev-&gt;rep[REP_DELAY] &amp;&amp; !dev-&gt;<span style="color: #000000;">rep[REP_PERIOD]) {
</span><span style="color: #008080;"> 67</span>         dev-&gt;timer.data = (<span style="color: #0000ff;">long</span><span style="color: #000000;">) dev;
</span><span style="color: #008080;"> 68</span>         dev-&gt;timer.function =<span style="color: #000000;"> input_repeat_key;
</span><span style="color: #008080;"> 69</span>         dev-&gt;rep[REP_DELAY] = <span style="color: #800080;">250</span><span style="color: #000000;">;
</span><span style="color: #008080;"> 70</span>         dev-&gt;rep[REP_PERIOD] = <span style="color: #800080;">33</span><span style="color: #000000;">;
</span><span style="color: #008080;"> 71</span> <span style="color: #000000;">    }
</span><span style="color: #008080;"> 72</span> 
<span style="color: #008080;"> 73</span>     <span style="color: #0000ff;">if</span> (!dev-&gt;<span style="color: #000000;">getkeycode)
</span><span style="color: #008080;"> 74</span>         dev-&gt;getkeycode =<span style="color: #000000;"> input_default_getkeycode;
</span><span style="color: #008080;"> 75</span> 
<span style="color: #008080;"> 76</span>     <span style="color: #0000ff;">if</span> (!dev-&gt;<span style="color: #000000;">setkeycode)
</span><span style="color: #008080;"> 77</span>         dev-&gt;setkeycode =<span style="color: #000000;"> input_default_setkeycode;
</span><span style="color: #008080;"> 78</span> 
<span style="color: #008080;"> 79</span>     error = device_add(&amp;dev-&gt;<span style="color: #000000;">dev);
</span><span style="color: #008080;"> 80</span>     <span style="color: #0000ff;">if</span><span style="color: #000000;"> (error)
</span><span style="color: #008080;"> 81</span>         <span style="color: #0000ff;">goto</span><span style="color: #000000;"> err_free_vals;
</span><span style="color: #008080;"> 82</span> 
<span style="color: #008080;"> 83</span>     path = kobject_get_path(&amp;dev-&gt;<span style="color: #000000;">dev.kobj, GFP_KERNEL);
</span><span style="color: #008080;"> 84</span>     pr_info(<span style="color: #800000;">"</span><span style="color: #800000;">%s as %s\n</span><span style="color: #800000;">"</span><span style="color: #000000;">,
</span><span style="color: #008080;"> 85</span>         dev-&gt;name ? dev-&gt;name : <span style="color: #800000;">"</span><span style="color: #800000;">Unspecified device</span><span style="color: #800000;">"</span><span style="color: #000000;">,
</span><span style="color: #008080;"> 86</span>         path ? path : <span style="color: #800000;">"</span><span style="color: #800000;">N/A</span><span style="color: #800000;">"</span><span style="color: #000000;">);
</span><span style="color: #008080;"> 87</span> <span style="color: #000000;">    kfree(path);
</span><span style="color: #008080;"> 88</span> 
<span style="color: #008080;"> 89</span>     error = mutex_lock_interruptible(&amp;<span style="color: #000000;">input_mutex);
</span><span style="color: #008080;"> 90</span>     <span style="color: #0000ff;">if</span><span style="color: #000000;"> (error)
</span><span style="color: #008080;"> 91</span>         <span style="color: #0000ff;">goto</span><span style="color: #000000;"> err_device_del;
</span><span style="color: #008080;"> 92</span>     
<span style="color: #008080;"> 93</span>     <span style="color: #008000;">/*</span><span style="color: #008000;"> 重要:把设备挂到全局的input子系统设备链表input_dev_list上 </span><span style="color: #008000;">*/</span>    
<span style="color: #008080;"> 94</span>     list_add_tail(&amp;dev-&gt;node, &amp;<span style="color: #000000;">input_dev_list);
</span><span style="color: #008080;"> 95</span> 
<span style="color: #008080;"> 96</span>     <span style="color: #008000;">/*</span><span style="color: #008000;"> 核心重点，input设备在增加到input_dev_list链表上之后，会查找 
</span><span style="color: #008080;"> 97</span> <span style="color: #008000;">     * input_handler_list事件处理链表上的handler进行匹配，这里的匹配 
</span><span style="color: #008080;"> 98</span> <span style="color: #008000;">     * 方式与设备模型的device和driver匹配过程很相似</span><span style="color: #008000;">*/</span>  
<span style="color: #008080;"> 99</span>     list_for_each_entry(handler, &amp;<span style="color: #000000;">input_handler_list, node)
</span><span style="color: #008080;">100</span>         input_attach_handler(dev, handler);<span style="color: #008000;">/*</span><span style="color: #008000;">遍历input_handler_list，通过input_match_device试图与每一个handler进行匹配 匹配上了就使用connect连接</span><span style="color: #008000;">*/</span>
<span style="color: #008080;">101</span>     <span style="color: #008000;">/*</span>
<span style="color: #008080;">102</span> <span style="color: #008000;">    static int input_attach_handler(struct input_dev *dev, struct input_handler *handler)
</span><span style="color: #008080;">103</span> <span style="color: #008000;">    {
</span><span style="color: #008080;">104</span> <span style="color: #008000;">        const struct input_device_id *id;
</span><span style="color: #008080;">105</span> <span style="color: #008000;">        int error;
</span><span style="color: #008080;">106</span> 
<span style="color: #008080;">107</span> <span style="color: #008000;">        id = input_match_device(handler, dev);
</span><span style="color: #008080;">108</span> <span style="color: #008000;">        if (!id)
</span><span style="color: #008080;">109</span> <span style="color: #008000;">            return -ENODEV;
</span><span style="color: #008080;">110</span> 
<span style="color: #008080;">111</span> <span style="color: #008000;">        error = handler-&gt;connect(handler, dev, id);
</span><span style="color: #008080;">112</span> <span style="color: #008000;">        if (error &amp;&amp; error != -ENODEV)
</span><span style="color: #008080;">113</span> <span style="color: #008000;">            pr_err("failed to attach handler %s to device %s, error: %d\n",
</span><span style="color: #008080;">114</span> <span style="color: #008000;">                   handler-&gt;name, kobject_name(&amp;dev-&gt;dev.kobj), error);
</span><span style="color: #008080;">115</span> 
<span style="color: #008080;">116</span> <span style="color: #008000;">        return error;
</span><span style="color: #008080;">117</span> <span style="color: #008000;">    }
</span><span style="color: #008080;">118</span>     <span style="color: #008000;">*/</span>
<span style="color: #008080;">119</span>     
<span style="color: #008080;">120</span> <span style="color: #000000;">    input_wakeup_procfs_readers();
</span><span style="color: #008080;">121</span> 
<span style="color: #008080;">122</span>     mutex_unlock(&amp;<span style="color: #000000;">input_mutex);
</span><span style="color: #008080;">123</span> 
<span style="color: #008080;">124</span>     <span style="color: #0000ff;">if</span> (dev-&gt;<span style="color: #000000;">devres_managed) {
</span><span style="color: #008080;">125</span>         dev_dbg(dev-&gt;dev.parent, <span style="color: #800000;">"</span><span style="color: #800000;">%s: registering %s with devres.\n</span><span style="color: #800000;">"</span><span style="color: #000000;">,
</span><span style="color: #008080;">126</span>             __func__, dev_name(&amp;dev-&gt;<span style="color: #000000;">dev));
</span><span style="color: #008080;">127</span>         devres_add(dev-&gt;<span style="color: #000000;">dev.parent, devres);
</span><span style="color: #008080;">128</span> <span style="color: #000000;">    }
</span><span style="color: #008080;">129</span>     <span style="color: #0000ff;">return</span> <span style="color: #800080;">0</span><span style="color: #000000;">;
</span><span style="color: #008080;">130</span> 
<span style="color: #008080;">131</span> <span style="color: #000000;">err_device_del:
</span><span style="color: #008080;">132</span>     device_del(&amp;dev-&gt;<span style="color: #000000;">dev);
</span><span style="color: #008080;">133</span> <span style="color: #000000;">err_free_vals:
</span><span style="color: #008080;">134</span>     kfree(dev-&gt;<span style="color: #000000;">vals);
</span><span style="color: #008080;">135</span>     dev-&gt;vals =<span style="color: #000000;"> NULL;
</span><span style="color: #008080;">136</span> <span style="color: #000000;">err_devres_free:
</span><span style="color: #008080;">137</span> <span style="color: #000000;">    devres_free(devres);
</span><span style="color: #008080;">138</span>     <span style="color: #0000ff;">return</span><span style="color: #000000;"> error;
</span><span style="color: #008080;">139</span> <span style="color: #000000;">}
</span><span style="color: #008080;">140</span> EXPORT_SYMBOL(input_register_device);</pre>
</div>
<h2>3.2注册handler</h2>
<p>一般handler不需要我们自己写 内核里面已经有了很多的hanlder基本够用</p>
下面以Evdev为例，来分析事件处理层。<br />
vim drivers/input/evdev.c</div>
<div>
<div class="cnblogs_code">
<pre><span style="color: #008080;"> 1</span> <span style="color: #0000ff;">static</span> <span style="color: #0000ff;">const</span> <span style="color: #0000ff;">struct</span> input_device_id evdev_ids[] =<span style="color: #000000;"> {
</span><span style="color: #008080;"> 2</span>     { .driver_info = <span style="color: #800080;">1</span> },    <span style="color: #008000;">/*</span><span style="color: #008000;"> Matches all devices </span><span style="color: #008000;">*/</span>
<span style="color: #008080;"> 3</span>     { },            <span style="color: #008000;">/*</span><span style="color: #008000;"> Terminating zero entry </span><span style="color: #008000;">*/</span>
<span style="color: #008080;"> 4</span> <span style="color: #000000;">};
</span><span style="color: #008080;"> 5</span> 
<span style="color: #008080;"> 6</span> <span style="color: #000000;">MODULE_DEVICE_TABLE(input, evdev_ids);
</span><span style="color: #008080;"> 7</span> 
<span style="color: #008080;"> 8</span> <span style="color: #0000ff;">static</span> <span style="color: #0000ff;">struct</span> input_handler evdev_handler =<span style="color: #000000;"> {
</span><span style="color: #008080;"> 9</span>     .<span style="color: #0000ff;">event</span>        =<span style="color: #000000;"> evdev_event,
</span><span style="color: #008080;">10</span>     .events        =<span style="color: #000000;"> evdev_events,
</span><span style="color: #008080;">11</span>     .connect    =<span style="color: #000000;"> evdev_connect,
</span><span style="color: #008080;">12</span>     .disconnect    =<span style="color: #000000;"> evdev_disconnect,
</span><span style="color: #008080;">13</span>     .legacy_minors    = <span style="color: #0000ff;">true</span><span style="color: #000000;">,
</span><span style="color: #008080;">14</span>     .minor        =<span style="color: #000000;"> EVDEV_MINOR_BASE,
</span><span style="color: #008080;">15</span>     .name        = <span style="color: #800000;">"</span><span style="color: #800000;">evdev</span><span style="color: #800000;">"</span><span style="color: #000000;">,
</span><span style="color: #008080;">16</span>     .id_table    =<span style="color: #000000;"> evdev_ids,
</span><span style="color: #008080;">17</span> <span style="color: #000000;">};
</span><span style="color: #008080;">18</span> 
<span style="color: #008080;">19</span> <span style="color: #0000ff;">static</span> <span style="color: #0000ff;">int</span> __init evdev_init(<span style="color: #0000ff;">void</span><span style="color: #000000;">)
</span><span style="color: #008080;">20</span> <span style="color: #000000;">{
</span><span style="color: #008080;">21</span>     <span style="color: #0000ff;">return</span> input_register_handler(&amp;<span style="color: #000000;">evdev_handler);
</span><span style="color: #008080;">22</span> <span style="color: #000000;">}
</span><span style="color: #008080;">23</span> 
<span style="color: #008080;">24</span> <span style="color: #0000ff;">static</span> <span style="color: #0000ff;">void</span> __exit evdev_exit(<span style="color: #0000ff;">void</span><span style="color: #000000;">)
</span><span style="color: #008080;">25</span> <span style="color: #000000;">{
</span><span style="color: #008080;">26</span>     input_unregister_handler(&amp;<span style="color: #000000;">evdev_handler);
</span><span style="color: #008080;">27</span> <span style="color: #000000;">}
</span><span style="color: #008080;">28</span> 
<span style="color: #008080;">29</span> <span style="color: #000000;">module_init(evdev_init);
</span><span style="color: #008080;">30</span> <span style="color: #000000;">module_exit(evdev_exit);
</span><span style="color: #008080;">31</span> 
<span style="color: #008080;">32</span> MODULE_AUTHOR(<span style="color: #800000;">"</span><span style="color: #800000;">Vojtech Pavlik &lt;vojtech@ucw.cz&gt;</span><span style="color: #800000;">"</span><span style="color: #000000;">);
</span><span style="color: #008080;">33</span> MODULE_DESCRIPTION(<span style="color: #800000;">"</span><span style="color: #800000;">Input driver event char devices</span><span style="color: #800000;">"</span><span style="color: #000000;">);
</span><span style="color: #008080;">34</span> MODULE_LICENSE(<span style="color: #800000;">"</span><span style="color: #800000;">GPL</span><span style="color: #800000;">"</span>);</pre>
</div>
<p>注册的handler可以在proc/bus/input/danlder中查看到</p>
</div>
<p><img src="Linux-input子系统/2909691-20220819102740731-2036281828.png" alt="" /></p>
<div class="cnblogs_code">
<pre><span style="color: #008080;"> 1</span> <span style="color: #008000;">/*</span><span style="color: #008000;">*
</span><span style="color: #008080;"> 2</span> <span style="color: #008000;"> * input_register_handler - register a new input handler
</span><span style="color: #008080;"> 3</span> <span style="color: #008000;"> * @handler: handler to be registered
</span><span style="color: #008080;"> 4</span> <span style="color: #008000;"> *
</span><span style="color: #008080;"> 5</span> <span style="color: #008000;"> * This function registers a new input handler (interface) for input
</span><span style="color: #008080;"> 6</span> <span style="color: #008000;"> * devices in the system and attaches it to all input devices that
</span><span style="color: #008080;"> 7</span> <span style="color: #008000;"> * are compatible with the handler.
</span><span style="color: #008080;"> 8</span>  <span style="color: #008000;">*/</span>
<span style="color: #008080;"> 9</span> <span style="color: #0000ff;">int</span> input_register_handler(<span style="color: #0000ff;">struct</span> input_handler *<span style="color: #000000;">handler)
</span><span style="color: #008080;">10</span> <span style="color: #000000;">{
</span><span style="color: #008080;">11</span>     <span style="color: #0000ff;">struct</span> input_dev *<span style="color: #000000;">dev;
</span><span style="color: #008080;">12</span>     <span style="color: #0000ff;">int</span><span style="color: #000000;"> error;
</span><span style="color: #008080;">13</span> 
<span style="color: #008080;">14</span>     error = mutex_lock_interruptible(&amp;<span style="color: #000000;">input_mutex);
</span><span style="color: #008080;">15</span>     <span style="color: #0000ff;">if</span><span style="color: #000000;"> (error)
</span><span style="color: #008080;">16</span>         <span style="color: #0000ff;">return</span><span style="color: #000000;"> error;
</span><span style="color: #008080;">17</span> 
<span style="color: #008080;">18</span>     INIT_LIST_HEAD(&amp;handler-&gt;<span style="color: #000000;">h_list);
</span><span style="color: #008080;">19</span> 　　<code class="  language-rust"><span class="token comment">/* `重要`:把设备处理器挂到全局的input子系统设备链表input_handler_list上 */ </span></code>
<span style="color: #008080;">20</span>     list_add_tail(&amp;handler-&gt;node, &amp;<span style="color: #000000;">input_handler_list);
</span><span style="color: #008080;">21</span> 　　<code class="  language-rust"><span class="token comment">/*遍历input_dev_list，试图与每一个input_dev进行匹配*/</span></code>
<span style="color: #008080;">22</span>     list_for_each_entry(dev, &amp;<span style="color: #000000;">input_dev_list, node)
</span><span style="color: #008080;">23</span> <span style="color: #000000;">        input_attach_handler(dev, handler);<br />　　　　/*<br /></span><code class="  language-objectivec"><span class="token keyword">static <span class="token keyword">int <span class="token function">input_attach_handler<span class="token punctuation">(<span class="token keyword">struct input_dev <span class="token operator">*dev<span class="token punctuation">, <span class="token keyword">struct input_handler <span class="token operator">*handler<span class="token punctuation">)
<span class="token punctuation">{
    <span class="token keyword">const <span class="token keyword">struct input_device_id <span class="token operator">*id<span class="token punctuation">;
    <span class="token keyword">int error<span class="token punctuation">;

    <span class="token comment">/* 利用handler-&gt;id_table和dev进行匹配*/
    id <span class="token operator">= <span class="token function">input_match_device<span class="token punctuation">(handler<span class="token punctuation">, dev<span class="token punctuation">)<span class="token punctuation">;
    <span class="token keyword">if <span class="token punctuation">(<span class="token operator">!id<span class="token punctuation">)
        <span class="token keyword">return <span class="token operator">-ENODEV<span class="token punctuation">;
      <span class="token comment">/*匹配成功，则调用handler-&gt;connect函数进行连接*/
    error <span class="token operator">= handler<span class="token operator">-&gt;<span class="token function">connect<span class="token punctuation">(handler<span class="token punctuation">, dev<span class="token punctuation">, id<span class="token punctuation">)<span class="token punctuation">;
    <span class="token keyword">if <span class="token punctuation">(error <span class="token operator">&amp;&amp; error <span class="token operator">!= <span class="token operator">-ENODEV<span class="token punctuation">)
        <span class="token function">pr_err<span class="token punctuation">(<span class="token string">"failed to attach handler %s to device %s, error: %d\n"<span class="token punctuation">,
               handler<span class="token operator">-&gt;name<span class="token punctuation">, <span class="token function">kobject_name<span class="token punctuation">(<span class="token operator">&amp;dev<span class="token operator">-&gt;dev<span class="token punctuation">.kobj<span class="token punctuation">)<span class="token punctuation">, error<span class="token punctuation">)<span class="token punctuation">;

    <span class="token keyword">return error<span class="token punctuation">;
<span class="token punctuation">}</span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></code><span style="color: #000000;"><br />　　　　　　*/
</span><span style="color: #008080;">24</span> 
<span style="color: #008080;">25</span> <span style="color: #000000;">    input_wakeup_procfs_readers();
</span><span style="color: #008080;">26</span> 
<span style="color: #008080;">27</span>     mutex_unlock(&amp;<span style="color: #000000;">input_mutex);
</span><span style="color: #008080;">28</span>     <span style="color: #0000ff;">return</span> <span style="color: #800080;">0</span><span style="color: #000000;">;
</span><span style="color: #008080;">29</span> <span style="color: #000000;">}
</span><span style="color: #008080;">30</span> EXPORT_SYMBOL(input_register_handler);</pre>
</div>
<p>这个过程和注册dev及其相似</p>
<h2>3.3 handler的connect函数</h2>
<div class="cnblogs_code">
<pre><span style="color: #008080;"> 1</span> <span style="color: #0000ff;">static</span> <span style="color: #0000ff;">int</span> evdev_connect(<span style="color: #0000ff;">struct</span> input_handler *handler, <span style="color: #0000ff;">struct</span> input_dev *<span style="color: #000000;">dev,
</span><span style="color: #008080;"> 2</span>              <span style="color: #0000ff;">const</span> <span style="color: #0000ff;">struct</span> input_device_id *<span style="color: #000000;">id)
</span><span style="color: #008080;"> 3</span> <span style="color: #000000;">{
</span><span style="color: #008080;"> 4</span>     <span style="color: #0000ff;">struct</span> evdev *<span style="color: #000000;">evdev;
</span><span style="color: #008080;"> 5</span>     <span style="color: #0000ff;">int</span><span style="color: #000000;"> minor;
</span><span style="color: #008080;"> 6</span>     <span style="color: #0000ff;">int</span><span style="color: #000000;"> dev_no;
</span><span style="color: #008080;"> 7</span>     <span style="color: #0000ff;">int</span><span style="color: #000000;"> error;
</span><span style="color: #008080;"> 8</span>     
<span style="color: #008080;"> 9</span>     <span style="color: #008000;">/*</span><span style="color: #008000;">申请一个新的次设备号</span><span style="color: #008000;">*/</span>
<span style="color: #008080;">10</span>     minor = input_get_new_minor(EVDEV_MINOR_BASE, EVDEV_MINORS, <span style="color: #0000ff;">true</span><span style="color: #000000;">);
</span><span style="color: #008080;">11</span> 
<span style="color: #008080;">12</span>     <span style="color: #008000;">/*</span><span style="color: #008000;"> 这说明内核已经没办法再分配这种类型的设备了 </span><span style="color: #008000;">*/</span> 
<span style="color: #008080;">13</span>     <span style="color: #0000ff;">if</span> (minor &lt; <span style="color: #800080;">0</span><span style="color: #000000;">) {
</span><span style="color: #008080;">14</span>         error =<span style="color: #000000;"> minor;
</span><span style="color: #008080;">15</span>         pr_err(<span style="color: #800000;">"</span><span style="color: #800000;">failed to reserve new minor: %d\n</span><span style="color: #800000;">"</span><span style="color: #000000;">, error);
</span><span style="color: #008080;">16</span>         <span style="color: #0000ff;">return</span><span style="color: #000000;"> error;
</span><span style="color: #008080;">17</span> <span style="color: #000000;">    }
</span><span style="color: #008080;">18</span> 
<span style="color: #008080;">19</span>     <span style="color: #008000;">/*</span><span style="color: #008000;"> 开始给evdev事件层驱动分配空间了 </span><span style="color: #008000;">*/</span>  
<span style="color: #008080;">20</span>     evdev = kzalloc(<span style="color: #0000ff;">sizeof</span>(<span style="color: #0000ff;">struct</span><span style="color: #000000;"> evdev), GFP_KERNEL);
</span><span style="color: #008080;">21</span>     <span style="color: #0000ff;">if</span> (!<span style="color: #000000;">evdev) {
</span><span style="color: #008080;">22</span>         error = -<span style="color: #000000;">ENOMEM;
</span><span style="color: #008080;">23</span>         <span style="color: #0000ff;">goto</span><span style="color: #000000;"> err_free_minor;
</span><span style="color: #008080;">24</span> <span style="color: #000000;">    }
</span><span style="color: #008080;">25</span> 
<span style="color: #008080;">26</span>         <span style="color: #008000;">/*</span><span style="color: #008000;"> 初始化client_list列表和evdev_wait队列 </span><span style="color: #008000;">*/</span>  
<span style="color: #008080;">27</span>     INIT_LIST_HEAD(&amp;evdev-&gt;<span style="color: #000000;">client_list);
</span><span style="color: #008080;">28</span>     spin_lock_init(&amp;evdev-&gt;<span style="color: #000000;">client_lock);
</span><span style="color: #008080;">29</span>     mutex_init(&amp;evdev-&gt;<span style="color: #000000;">mutex);
</span><span style="color: #008080;">30</span>     init_waitqueue_head(&amp;evdev-&gt;<span style="color: #000000;">wait);
</span><span style="color: #008080;">31</span>     evdev-&gt;exist = <span style="color: #0000ff;">true</span><span style="color: #000000;">;
</span><span style="color: #008080;">32</span> 
<span style="color: #008080;">33</span>     dev_no =<span style="color: #000000;"> minor;
</span><span style="color: #008080;">34</span>     <span style="color: #008000;">/*</span><span style="color: #008000;"> Normalize device number if it falls into legacy range </span><span style="color: #008000;">*/</span>
<span style="color: #008080;">35</span>     <span style="color: #0000ff;">if</span> (dev_no &lt; EVDEV_MINOR_BASE +<span style="color: #000000;"> EVDEV_MINORS)
</span><span style="color: #008080;">36</span>         dev_no -=<span style="color: #000000;"> EVDEV_MINOR_BASE;
</span><span style="color: #008080;">37</span>     
<span style="color: #008080;">38</span>     <span style="color: #008000;">/*</span><span style="color: #008000;">设置设备节点名称，/dev/eventX 就是在此时设置</span><span style="color: #008000;">*/</span>
<span style="color: #008080;">39</span>     dev_set_name(&amp;evdev-&gt;dev, <span style="color: #800000;">"</span><span style="color: #800000;">event%d</span><span style="color: #800000;">"</span><span style="color: #000000;">, dev_no);
</span><span style="color: #008080;">40</span> 
<span style="color: #008080;">41</span>     <span style="color: #008000;">/*</span><span style="color: #008000;"> 初始化evdev结构体，其中handle为输入设备和事件处理的关联接口 </span><span style="color: #008000;">*/</span>  
<span style="color: #008080;">42</span>     evdev-&gt;handle.dev =<span style="color: #000000;"> input_get_device(dev);
</span><span style="color: #008080;">43</span>     evdev-&gt;handle.name = dev_name(&amp;evdev-&gt;<span style="color: #000000;">dev);
</span><span style="color: #008080;">44</span>     evdev-&gt;handle.handler =<span style="color: #000000;"> handler;
</span><span style="color: #008080;">45</span>     evdev-&gt;handle.<span style="color: #0000ff;">private</span> =<span style="color: #000000;"> evdev;
</span><span style="color: #008080;">46</span> 
<span style="color: #008080;">47</span>       <span style="color: #008000;">/*</span><span style="color: #008000;">设置设备号，应用层就是通过设备号，找到该设备的</span><span style="color: #008000;">*/</span>
<span style="color: #008080;">48</span>     evdev-&gt;dev.devt =<span style="color: #000000;"> MKDEV(INPUT_MAJOR, minor);
</span><span style="color: #008080;">49</span>     evdev-&gt;dev.<span style="color: #0000ff;">class</span> = &amp;<span style="color: #000000;">input_class;
</span><span style="color: #008080;">50</span>     evdev-&gt;dev.parent = &amp;dev-&gt;<span style="color: #000000;">dev;
</span><span style="color: #008080;">51</span>     evdev-&gt;dev.release =<span style="color: #000000;"> evdev_free;
</span><span style="color: #008080;">52</span>     device_initialize(&amp;evdev-&gt;<span style="color: #000000;">dev);
</span><span style="color: #008080;">53</span> 
<span style="color: #008080;">54</span>      <span style="color: #008000;">/*</span><span style="color: #008000;"> input_dev设备驱动和handler事件处理层的关联，就在这时由handle完成 </span><span style="color: #008000;">*/</span> 
<span style="color: #008080;">55</span>     error = input_register_handle(&amp;evdev-&gt;<span style="color: #000000;">handle);
</span><span style="color: #008080;">56</span>     <span style="color: #0000ff;">if</span><span style="color: #000000;"> (error)
</span><span style="color: #008080;">57</span>         <span style="color: #0000ff;">goto</span><span style="color: #000000;"> err_free_evdev;
</span><span style="color: #008080;">58</span> 
<span style="color: #008080;">59</span>     cdev_init(&amp;evdev-&gt;cdev, &amp;<span style="color: #000000;">evdev_fops);
</span><span style="color: #008080;">60</span>     evdev-&gt;cdev.kobj.parent = &amp;evdev-&gt;<span style="color: #000000;">dev.kobj;
</span><span style="color: #008080;">61</span>     error = cdev_add(&amp;evdev-&gt;cdev, evdev-&gt;dev.devt, <span style="color: #800080;">1</span><span style="color: #000000;">);
</span><span style="color: #008080;">62</span>     <span style="color: #0000ff;">if</span><span style="color: #000000;"> (error)
</span><span style="color: #008080;">63</span>         <span style="color: #0000ff;">goto</span><span style="color: #000000;"> err_unregister_handle;
</span><span style="color: #008080;">64</span> 
<span style="color: #008080;">65</span>     <span style="color: #008000;">/*</span><span style="color: #008000;">将设备加入到Linux设备模型，它的内部将找到它的bus，然后让它的bus
</span><span style="color: #008080;">66</span> <span style="color: #008000;">    给它找到它的driver，在驱动或者总线的probe函数中，一般会在/dev/目录
</span><span style="color: #008080;">67</span> <span style="color: #008000;">    先创建相应的设备节点，这样应用程序就可以通过该设备节点来使用设备了
</span><span style="color: #008080;">68</span> <span style="color: #008000;">    ，/dev/eventX 设备节点就是在此时生成
</span><span style="color: #008080;">69</span>     <span style="color: #008000;">*/</span>
<span style="color: #008080;">70</span>     error = device_add(&amp;evdev-&gt;<span style="color: #000000;">dev);
</span><span style="color: #008080;">71</span>     <span style="color: #0000ff;">if</span><span style="color: #000000;"> (error)
</span><span style="color: #008080;">72</span>         <span style="color: #0000ff;">goto</span><span style="color: #000000;"> err_cleanup_evdev;
</span><span style="color: #008080;">73</span> 
<span style="color: #008080;">74</span>     <span style="color: #0000ff;">return</span> <span style="color: #800080;">0</span><span style="color: #000000;">;
</span><span style="color: #008080;">75</span> 
<span style="color: #008080;">76</span> <span style="color: #000000;"> err_cleanup_evdev:
</span><span style="color: #008080;">77</span> <span style="color: #000000;">    evdev_cleanup(evdev);
</span><span style="color: #008080;">78</span> <span style="color: #000000;"> err_unregister_handle:
</span><span style="color: #008080;">79</span>     input_unregister_handle(&amp;evdev-&gt;<span style="color: #000000;">handle);
</span><span style="color: #008080;">80</span> <span style="color: #000000;"> err_free_evdev:
</span><span style="color: #008080;">81</span>     put_device(&amp;evdev-&gt;<span style="color: #000000;">dev);
</span><span style="color: #008080;">82</span> <span style="color: #000000;"> err_free_minor:
</span><span style="color: #008080;">83</span> <span style="color: #000000;">    input_free_minor(minor);
</span><span style="color: #008080;">84</span>     <span style="color: #0000ff;">return</span><span style="color: #000000;"> error;
</span><span style="color: #008080;">85</span> }</pre>
</div>
<p>over</p>
<h1>4.应用层的角度分析到底层</h1>
<p>evdev_read（）---------------------------》wait_event_interruptible(evdev-&gt;wait,client-&gt;packet_head != client-&gt;tail || !evdev-&gt;exist || client-&gt;revoked);等待evdev-&gt;wait唤醒</p>
<p>　　evdev_pass_values-----------------------》wake_up_interruptible(&amp;evdev-&gt;wait);</p>
<p>　　　　evdev_events---------------------------》evdev_pass_values(client, vals, count, ev_time);<br />　　　　　　evdev_event----------------------------》evdev_events(handle, vals, 1);</p>
<p>　　　　　　　　static struct input_handler evdev_handler = {<br />&nbsp;&nbsp; 　　　　　　　　&nbsp;.event&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;= evdev_event,<br />&nbsp;&nbsp; &nbsp;　　　　　　　　.events&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;= evdev_events,<br />&nbsp;&nbsp; 　　　　　　　　&nbsp;.connect&nbsp;&nbsp; &nbsp;= evdev_connect,<br />&nbsp;&nbsp; &nbsp;　　　　　　　　.disconnect&nbsp;&nbsp; &nbsp;= evdev_disconnect,<br />&nbsp;&nbsp; 　　　　　　　　&nbsp;.legacy_minors&nbsp;&nbsp; &nbsp;= true,<br />&nbsp;&nbsp; &nbsp;　　　　　　　　.minor&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;= EVDEV_MINOR_BASE,<br />&nbsp;&nbsp; &nbsp;　　　　　　　　.name&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;= "evdev",<br />&nbsp;&nbsp; &nbsp;　　　　　　　　.id_table&nbsp;&nbsp; &nbsp;= evdev_ids,<br />　　　　　　　　};</p>
<p>　　　　　　　　input_to_handler-----------------------------》　　 if (handler-&gt;events)<br />&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;　　　　　　　　　　　　　　　　　　　　　　　　　　　　handler-&gt;events(handle, vals, count);<br />&nbsp;&nbsp; &nbsp;　　　　　　　　　　　　　　　　　　　　　　　　　　　else if (handler-&gt;event)<br />&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;　　　　　　　　　　　　　　　　　　　　　　　　　　　　for (v = vals; v != vals + count; v++)<br />&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; 　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　&nbsp;handler-&gt;event(handle, v-&gt;type, v-&gt;code, v-&gt;value);</p>
<p>　　　　　　input_pass_values--------------------------------》count = input_to_handler(handle, vals, count);</p>
<p>　　input_handle_event----------------------------》input_pass_values(dev, dev-&gt;vals, dev-&gt;num_vals);</p>
</div>
<p>input_event----------------------------------------》input_handle_event(dev, type, code, value);</p>
<p>显然，就是input_dev通过输入核心为驱动层提供统一的接口，<code>input_event</code>，来向事件处理层上报数据并唤醒。</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
</div>
</div>
