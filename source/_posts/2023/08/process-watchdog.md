---
title: process-watchdog
top: false
cover: false
toc: true
mathjax: true
date: 2023-08-31 15:19:48
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

# watchdog作用
看门狗（Watchdog）是一种硬件或软件机制，旨在监视计算机系统或设备的运行状态，并在系统出现故障、死锁或异常情况时采取措施以防止系统长时间无响应或停滞。看门狗在嵌入式系统、服务器、网络设备等各种场景中都有广泛应用。

看门狗的主要作用包括：

1. **保证系统稳定性和可用性：** 看门狗能够监视系统的运行状态。如果系统在一段时间内没有及时响应看门狗的喂狗操作，看门狗会触发特定的操作，如系统重启或其他预定义的操作，以恢复系统的稳定性和可用性。

2. **防止死锁和异常状态：** 死锁是指系统中的进程或资源无法继续执行或释放，导致系统无法正常运行。看门狗能够监控这种异常情况，并在死锁发生时进行干预，防止系统长时间无响应。

3. **检测程序错误：** 看门狗还可以用于检测程序错误，比如内存泄漏、异常崩溃等。如果程序出现了无法处理的错误，可能无法执行喂狗操作，从而触发看门狗超时操作。

4. **恢复系统正常状态：** 当系统出现异常情况时，看门狗可以自动采取措施，如重启系统或执行预定的恢复操作，以使系统重新进入正常状态。

5. **预防设备故障：** 在一些嵌入式系统中，看门狗还可以监控硬件设备的状态。如果硬件设备发生故障或停滞，看门狗可以采取措施避免系统长时间受到影响。

总之，看门狗是一种用于提高系统稳定性、可靠性和可用性的重要机制。它能够在系统遇到异常情况时自动采取措施，保障系统能够快速恢复正常运行。

# watchdog源码
设备树节点:
```c
   wdog1: wdog@020bc000 {
    compatible = "fsl,imx6ul-wdt", "fsl,imx21-wdt";
    reg = <0x020bc000 0x4000>;
    interrupts = <0 80 4>;
    clocks = <&clks 208>;
   };

   wdog2: wdog@020c0000 {
    compatible = "fsl,imx6ul-wdt", "fsl,imx21-wdt";
    reg = <0x020c0000 0x4000>;
    interrupts = <0 81 4>;
    clocks = <&clks 209>;
    status = "disabled";
   };
```
这段代码片段是设备树（Device Tree）中的一个节点，描述了一个 i.MX6 UltraLite 系列处理器上的看门狗设备（Watchdog Device）的属性和配置。让我为你解释其中的内容：

- `wdog1: wdog@020bc000 { ... };`：这是一个设备节点的定义，其中 `wdog1` 是节点的名称，`wdog@020bc000` 是看门狗设备在设备树中的标识，`020bc000` 是设备的寄存器基地址。

- `compatible = "fsl,imx6ul-wdt", "fsl,imx21-wdt";`：这是设备兼容性属性，表示这个设备与两种类型的看门狗兼容，即 i.MX6 UltraLite 系列看门狗和 i.MX21 系列看门狗。

- `reg = <0x020bc000 0x4000>;`：这是设备的寄存器属性，指定设备的寄存器基地址和大小。在这里，寄存器基地址是 `0x020bc000`，大小是 `0x4000`（16KB）。

- `interrupts = <0 80 4>;`：这是中断属性，指定中断的描述信息。在这里，`0` 表示中断控制器编号，`80` 表示中断号，`4` 表示中断触发类型（边缘触发）。

- `clocks = <&clks 208>;`：这是时钟属性，指定看门狗设备所使用的时钟源。`&clks` 是时钟源的引用，`208` 是时钟源的索引或标识。

这个设备树节点描述了 i.MX6 UltraLite 系列处理器上的一个看门狗设备的属性，包括设备类型、寄存器地址、中断配置和时钟源等信息。设备树在嵌入式系统中用于描述硬件设备和资源配置，使得内核能够根据这些信息正确初始化和管理设备。

drivers/watchdog/imx2_wdt.c:imx2_wdt_probe()
```c
static int __init imx2_wdt_probe(struct platform_device *pdev)
{
	struct imx2_wdt_device *wdev;
	struct watchdog_device *wdog;
	struct resource *res;
	void __iomem *base;
	int ret;
	int irq;
	u32 val;
	struct device_node *of_node = pdev->dev.of_node;

	wdev = devm_kzalloc(&pdev->dev, sizeof(*wdev), GFP_KERNEL);
	if (!wdev)
		return -ENOMEM;

	res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	base = devm_ioremap_resource(&pdev->dev, res);
	if (IS_ERR(base))
		return PTR_ERR(base);

	wdev->regmap = devm_regmap_init_mmio_clk(&pdev->dev, NULL, base,
						 &imx2_wdt_regmap_config);
	if (IS_ERR(wdev->regmap)) {
		dev_err(&pdev->dev, "regmap init failed\n");
		return PTR_ERR(wdev->regmap);
	}

	wdev->clk = devm_clk_get(&pdev->dev, NULL);
	if (IS_ERR(wdev->clk)) {
		dev_err(&pdev->dev, "can't get Watchdog clock\n");
		return PTR_ERR(wdev->clk);
	}

	irq = platform_get_irq(pdev, 0);
	ret = devm_request_irq(&pdev->dev, irq, imx2_wdt_isr, 0,
			       dev_name(&pdev->dev), pdev);
	if (ret) {
		dev_err(&pdev->dev, "can't get irq %d\n", irq);
		return ret;
	}

	if (of_get_property(of_node, "fsl,wdog_b", NULL)) {
		wdev->wdog_b = true;
		dev_info(&pdev->dev, "use WDOG_B to reboot.\n");
	}

	wdog			= &wdev->wdog;
	wdog->info		= &imx2_wdt_info;
	wdog->ops		= &imx2_wdt_ops;
	wdog->min_timeout	= 1;
	wdog->max_timeout	= IMX2_WDT_MAX_TIME;

	clk_prepare_enable(wdev->clk);

	regmap_read(wdev->regmap, IMX2_WDT_WRSR, &val);
	wdog->bootstatus = val & IMX2_WDT_WRSR_TOUT ? WDIOF_CARDRESET : 0;

	wdog->timeout = clamp_t(unsigned, timeout, 1, IMX2_WDT_MAX_TIME);
	if (wdog->timeout != timeout)
		dev_warn(&pdev->dev, "Initial timeout out of range! Clamped from %u to %u\n",
			 timeout, wdog->timeout);

	platform_set_drvdata(pdev, wdog);
	watchdog_set_drvdata(wdog, wdev);
	watchdog_set_nowayout(wdog, nowayout);
	watchdog_init_timeout(wdog, timeout, &pdev->dev);
    //开启定时器定时喂狗
	setup_timer(&wdev->timer, imx2_wdt_timer_ping, (unsigned long)wdog);

	imx2_wdt_ping_if_active(wdog);

	/*
	 * Disable the watchdog power down counter at boot. Otherwise the power
	 * down counter will pull down the #WDOG interrupt line for one clock
	 * cycle.
	 */
	regmap_write(wdev->regmap, IMX2_WDT_WMCR, 0);

	ret = watchdog_register_device(wdog);
	if (ret) {
		dev_err(&pdev->dev, "cannot register watchdog device\n");
		return ret;
	}

	wdev->restart_handler.notifier_call = imx2_restart_handler;
	wdev->restart_handler.priority = 128;
	ret = register_restart_handler(&wdev->restart_handler);
	if (ret)
		dev_err(&pdev->dev, "cannot register restart handler\n");

	dev_info(&pdev->dev, "timeout %d sec (nowayout=%d)\n",
		 wdog->timeout, nowayout);

	return 0;
}
```
```shell
root@ATK-IMX6U:/proc# cat interrupts 
           CPU0       
 16:      39397       GPC  55 Level     i.MX Timer Tick
 17:      56353       GPC  13 Level     mxs-dma
 18:      18539       GPC  15 Level     bch
 19:          0       GPC  33 Level     2010000.ecspi
 20:       2871       GPC  26 Level     2020000.serial
 21:          0       GPC  98 Level     sai
 22:          0       GPC  50 Level     2034000.asrc
 48:          0  gpio-mxc  18 Edge      USER-KEY1
 49:          0  gpio-mxc  19 Edge      2190000.usdhc cd
198:          0       GPC   4 Level     20cc000.snvs:snvs-powerkey
199:      22953       GPC 120 Level     20b4000.ethernet
200:          0       GPC 121 Level     20b4000.ethernet
201:          0       GPC  80 Level     20bc000.wdog
204:          0       GPC  49 Level     imx_thermal
209:          0       GPC  19 Level     rtc alarm
215:          0       GPC   2 Level     sdma
220:          0       GPC  43 Level     2184000.usb
221:         35       GPC  42 Level     2184200.usb
222:       1342       GPC 118 Level     2188000.ethernet
223:          0       GPC 119 Level     2188000.ethernet
224:         52       GPC  22 Level     mmc0
225:         10       GPC  36 Level     21a0000.i2c
226:         34       GPC  37 Level     21a4000.i2c
229:          3       GPC   5 Level     21c8000.lcdif
232:          0       GPC  28 Level     21ec000.serial
IPI0:          0  CPU wakeup interrupts
IPI1:          0  Timer broadcast interrupts
IPI2:          0  Rescheduling interrupts
IPI3:          0  Function call interrupts
IPI4:          0  Single function call interrupts
IPI5:          0  CPU stop interrupts
IPI6:          0  IRQ work interrupts
IPI7:          0  completion interrupts
Err:          0
```
看门狗的中断就是80,81的看门狗设备树中没有开.

# 控制watchdog
`/dev/watchdog` 文件通常用于控制和管理看门狗设备。通过对这个文件执行特定的操作，你可以喂狗、配置超时时间、重启系统等。以下是一些常见的操作方法：

1. **喂狗：** 对 `/dev/watchdog` 文件写入任意数据可以喂狗，即重置看门狗的计时器，防止看门狗超时。这通常用于告诉看门狗设备：“我还活着，不要触发超时”。

   ```sh
   echo 1 > /dev/watchdog
   ```

2. **设置超时时间：** 有些系统允许你设置 `/dev/watchdog` 文件的内容来改变看门狗的超时时间。这取决于系统和硬件平台的支持。例如，要设置超时时间为 10 秒：

   ```sh
   echo 10 > /dev/watchdog
   ```

   请注意，不是所有系统都支持通过写入 `/dev/watchdog` 来设置超时时间。

3. **关闭看门狗：** 关闭看门狗通常是通过停止对 `/dev/watchdog` 文件的写入操作来实现的。不再写入数据，看门狗计时器会在超时后触发。

   ```sh
   echo 0 > /dev/watchdog
   ```

4. **重启系统：** 在某些情况下，写入特定的数据到 `/dev/watchdog` 可以触发系统重启。这通常用于告诉看门狗设备：“我要重启系统”。

   ```sh
   echo "reboot" > /dev/watchdog
   ```

请注意，使用 `/dev/watchdog` 文件操作可能会需要足够的权限，通常需要以超级用户权限（使用 `sudo`）执行操作。此外，不同的系统和硬件平台可能会有不同的支持和行为，因此在执行任何操作之前，最好查阅相关文档以确保你了解正确的操作方法和效果。误操作可能会导致系统重启或其他不可预料的问题。
