---
layout: post
title: 讀懂了佛教的因緣法，就不會再相信有（絕對的）隨機事件、偶然事件了
wechat: 
description: 因緣法強調萬事萬物的產生和發展皆由因緣和合而成，即有其特定的因和緣（條件）。因此，一旦真正領悟了這種法則，就會明白所謂的“隨機事件”實際上也是在各種因緣的作用下發生的，並非毫無根源和規律的純粹偶然。
tags:
 - 因緣法
---

## 什麼是因緣法？

>《雜阿含經》卷第十三，335經：謂“此有故彼有，此起故彼起，……此無故彼無，此滅故彼滅……”。

白話：因為這個存在所以那個存在，這個生起所以那個生起；因為這個不存在所以那個不存在，這個消失所以那個消失。

基本含義：一切事物的產生（起）和存在（有），都依賴於其他事物的產生和存在。同樣地，當一切事物所依賴的環境發生變化時，它們也會發生變化，最終因為依賴的消亡而消亡，最後依賴不存在（無）了，事物本身也不存在了。換句話說，一切事物都不能獨立地產生和存在。

這就是佛教最最核心、最最重要、最最基本的因緣法。也叫緣起法。

## 為什麼不該相信有（絕對的）隨機事件？

什麼是隨機事件（或偶然事件）？就是的概率事件，它的結果完全不可預測，不可知，而由數學理論決定了某個情況發生的概率。

舉個例子，擲骰子。一般的棋牌遊戲中，如麻將，經常會有擲骰子的環節，由此來產生一個隨機數。決定從誰開始，或從哪個位置開始。

**那麼擲骰子的結果是隨機的嗎？**

對於普通人來說，是的。原因在於，普通人沒有經過專門的練習，也沒有作弊，骰子也是正常的骰子，那麼就是無法控制其結果是幾點，可能會在一到六之間的任何一個數。

如果有看過反賭節目或者特技人員的表演的話，就知道他們是可以完全控制骰子的點數的，這並不神奇，這只是長久的艱苦練習而達成的本領。

![反賭玩骰子](../images/2024-09-01-13-22-45.png)

很多普通人無法達成的事情，其實都有專人可以達成，比如扔撲克牌，有人就可以用撲克牌滅蠟燭。某音上就有很多飛牌的視頻。（請自行搜索。）

從因緣法的角度來說，這些並不難解釋。

回到擲骰子的例子，如果你能控制外部環境，使用固定的、一樣的骰子，沒有干擾的環境，沒有風，然後練習擲的姿勢和動作，只要把這些東西全部練習好了，那麼擲骰子的結果就可控了。結果可控後，那麼擲骰子就不再是隨機事件了。就可以像“反賭”節目中看到的那樣，想要幾點就得到幾點了。

相同的道理，我們普通人認為的“隨機事件”，其實是因為我們對這件事情產生的原因不清楚，或無法控制他的結果，因此，這件事情看起來就是“隨機事件”了。一旦，你找到了它的原理，看清楚了它的原因，能夠控制它的結果，那麼“隨機事件”就不再是“隨機事件”，而變成了“完全可控事件”了。

現代科學的進步幫助我們看清楚了越來越多的原因，對於有些自然現象也可以控制了，這在古人看起來是完全無法理解的，但是當今科技卻是很普遍的事情，比如人工降雨。例如，僅2023年吉林就進行8次大規模人工增雨作業（https://baijiahao.baidu.com/s?id=1788252768267571214&wfr=spider&for=pc）。

## 機器產生的隨機數是絕對的隨機數嗎？

這一節是寫給IT人士的，有計算機背景，或數學背景的人士看的。如果你看不懂，沒關係，直接跳過中間看小結就可以。

在Python中，通常random.random()產生隨機數。該函數生成一個範圍在 0.0 到 1.0 之間的偽隨機浮點數。該函數使用的是梅森旋轉算法（Mersenne Twister）。在一定程度，它就是隨機數。（就像前面，普通人擲骰子一樣）。

然而，這個算法產生的隨機數並不是絕對的，而是偽隨機數。看起來隨機，但實際上是可預測的，只要知道生成的算法和種子。如果想要更加“真實”的隨機數，必須使用“secrets.SystemRandom().random()”，它基於操作系統的熵源，如 /dev/urandom 或類似機制。（根據ChatGPT回答整理。）

然而，這個也不是“真”隨機數。它或許只是比上面一個隨機數更加不可預測。但距離真正的不可預測（即隨機性）還有距離。例如，如果很多大公司正在預研的量子計算機，一旦量子計算機研製成功，就可以破解經典計算機上所無法破解的算法了。

**小結**

目前計算機產生的隨機數，其實是偽隨機數，或者是以現代科技難以預測的“隨機數”而已，但如果有更先進的計算機，比如量子計算機，那麼現代經典計算機認為無法預測的數，就可以被量子計算機所預測 —— 從而不再是“真隨機數”了，同理，量子計算機產生的隨機數，也不是絕對的隨機數，因為可以被下一代更加先進的計算機所破解。

這就是科學發展的現狀和規律。沒有絕對的隨時數，只有不夠快的CPU（代指一切計算單元）。

## 總結

因緣法強調萬事萬物的產生和發展皆由因緣和合而成，即有其特定的因和緣（條件）。因此，一旦真正領悟了這種法則，就會明白所謂的“隨機事件”實際上也是在各種因緣的作用下發生的，並非毫無根源和規律的純粹偶然。

## 補充閱讀

[讀懂了佛教的因緣法，就不會再相信命運了 —— 包括宿命論、造物主、老天爺等](https://mp.weixin.qq.com/s/mvmWSx8zEwCkHCOGsccXyw) 


阿彌陀佛<br>
愚千一

