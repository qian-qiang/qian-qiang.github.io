---
title: IMX6ull 移植 lVGL总结
permalink: IMX6ull 移植 lVGL总结
top: false
cover: false
toc: true
mathjax: true
date: 2022-01-01 20:59:25
password:
summary:
tags:
- linux
- imx6ull
categories:
- linux
keywords:
description:
---
<h1>1 ：准备工作</h1>
<p>硬件：正点原子的Imx6ull开发板</p>
<p>环境：ubuntu18.0</p>
<p>lvgl软件地址：<a href="git@gitee.com:qian-qiang/imx6ull_lvgl_demo.git" target="_blank" rel="noopener">git@gitee.com:qian-qiang/imx6ull_lvgl_demo.git</a></p>
<h1>2：git 厂库修改文件</h1>
<p>2.1：修改文件lv_drv_config.h</p>
<p><img src="IMX6ull-移植-lVGL总结/2909691-20220928151916481-1456634923.png" alt="" height="513" width="1084" /></p>
<p><img src="IMX6ull-移植-lVGL总结/2909691-20220928152209724-1097250473.png" alt="" height="368" width="1087" /></p>
<p><img src="IMX6ull-移植-lVGL总结/2909691-20220928153140065-1807119912.png" alt="" height="177" width="1081" /></p>
<p id="1664350186406"></p>
<p id="1664349615994">2.2：修改文件lv_conf.h</p>
<p><img src="IMX6ull-移植-lVGL总结/2909691-20220928152957065-501054685.png" alt="" height="387" width="1664" /></p>
<p><img src="IMX6ull-移植-lVGL总结/2909691-20220928152945955-899676295.png" alt="" height="843" width="1671" /></p>
<p><img src="IMX6ull-移植-lVGL总结/2909691-20220928152922659-1842915282.png" alt="" /></p>
<p id="1664350048873">2.3：修改文件main.c</p>
<p><img src="IMX6ull-移植-lVGL总结/2909691-20220928153305849-1048335725.png" alt="" /></p>
<h1>3：make</h1>
<p>由于环境的问题 make过程中可能有问题 上百度应该改都能解决 最后生成demo文件&nbsp;</p>
<p><img src="IMX6ull-移植-lVGL总结/2909691-20220928153451220-1274979267.png" alt="" /></p>
<h1>4：scp到开发板运行即可</h1>
<p>&nbsp;</p>
<p id="1664350272125"></p>
<p id="1664349445067"></p>
<p>&nbsp;</p>
