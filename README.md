# V2EX - terminal

## Overview
这是一个基于终端的 [V2EX][v2ex] 客户端，使用 curses 库写的，可惜没有更多的 API，要不就可以完成一个比较完整的小工具了。
提供了几种不同的 logo 可以选择，可以在 `settings.vx` 文件中设置。

## Requirements
这是一个 python 程序，需要终端支持最少 8 种颜色，现在用的最多的 xterm, xterm-256color 等都没有问题，你可以运行 `echo $TERM` 命令来查看你使用的终端，在 Mac OS X 以及 GNU/Linux 系统上，你只需要运行如下命令来完成 yaml 库的安装：
    
    sudo pip install pyyaml

## Shortcuts
反引号开始，单引号结束的是 shortcut，左右方向键翻页，之所以用了方向键，是因为写这个程序的时候键盘上根本没有 Page Up 和 Page Down 这些键。

  * `h' Home
  * `r' Reload
  * `q' Quit
## Report Bugs
你可以在 [Github Issues](https://github.com/ratazzi/v2ex-terminal/issues) 报告 bug，最好附上程序日志的 [Pastebin][pastebin] 或者 [notepad.cc][notepadcc] 等的链接。
 
 [v2ex]: http://www.v2ex.com/ "V2EX"
 [pastebin]: http://pastebin.com "Pastebin"
 [notepadcc]: http://notepad.cc/ "nodepad.cc"

