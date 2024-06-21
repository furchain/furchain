### VNML Syntax Documentation

VNML (Visual Novel Markup Language) is a subset of XML, designed to create and manage interactive visual novel narratives. This document provides a comprehensive guide to the syntax and fields of VNML, along with illustrative examples. **Comments are mandatory and should be written in the same language as the character dialogues.**

### Syntax Overview

#### `<vnml lang="...">`

The root element that encapsulates the entire visual novel script. The `lang` attribute specifies the language used in comments and dialogues.

**Note**: Except for the `name` attribute, all other attributes should always be written in English.

##### Fields:

- **`<scene>`**: Specifies the initial scene settings and can appear multiple times to denote scene changes. This element is required and must appear at least once.
    - **`<background>`**: Describes the background scene using keywords.
        - **`keywords`**: A comma-separated list of keywords describing the background (e.g., "stormy night, abandoned mansion").
    - **`<music>`**: Describes the background music using keywords.
        - **`keywords`**: A comma-separated list of keywords describing the music, including instruments, genre, and era (e.g., "tense, orchestral, eerie, strings, 19th century").

- **`<dialogue>`**: Contains a mix of narration and dialogue. This element should exceed 50 lines and is required to appear at least once.
    - **`<narration>`**: Provides the narration text.
    - **`<character>`**: Contains the dialogue text in spoken style and describes the character's attributes.
        - **`name`**: The name of the speaking character.
        - **`identifier`**: Describes the character's basic information such as age, gender, and physical traits, excluding clothing and accessories (if different from the previous dialogue).
        - **`emotion`**: The character's emotion while speaking (if different from the previous dialogue).
        - **`clothes`**: A comma-separated list of items describing the character's current clothing and accessories (if different from the previous dialogue).

- **`<options>`**: Defines the user's multiple-choice options. This element is required and must appear at least once.
    - **`<title>`**: The title of the multiple-choice section.
    - **`<option>`**: Each option available for the user to choose.

- **`<action>`**: Specifies the user's selected action from the multiple-choice options. This element is required and follows the `<options>` element.

### Comments

In VNML, comments serve as a versatile tool for developers. They can be used as a scratchpad for jotting down thoughts, planning code structure, storing hints for future reference, and more. **Comments are mandatory and should be written in the same language as the character dialogues.**

### Example

```xml
<vnml lang="zh">
    <!-- 场景标签，定义初始场景设置。 -->
    <scene>
        <!-- 背景标签，使用关键词描述场景的背景。
             除了name属性，所有的attribute都应该是英文。
             注意："twilight" 可能会设置一种神秘和阴森的基调。 -->
        <background keywords="dense forest, ancient ruins, twilight, overgrown vines, crumbling structures"/>
        
        <!-- 音乐标签，使用关键词描述背景音乐。
             除了name属性，所有的attribute都应该是英文。 
             注意：音乐应与阴森的氛围相辅相成。 -->
        <music keywords="mysterious, tense, ambient, echoing, faint whispers, strings, 19th century"/>
    </scene>
    
    <!-- 对话标签，包含叙述和角色对话。
         除了name属性，所有的attribute都应该是英文。 
         注意：确保对话超过50行，以增加深度。 -->
    <dialogue>
        <!-- 叙述标签，用于提供叙述文本。
             设置场景并介绍角色的到来。 -->
        <narration>
            黄昏的薄雾在古老的废墟间弥漫，宛如一层轻纱笼罩在这片被遗忘的土地上。埃尔德里克、萨洛克和拉格娜三人悄然踏入，仿佛打扰了沉睡千年的幽灵。迷离的暮色中，废墟仿佛在低语，诉说着千年未解的秘密，令人不禁心生敬畏。
        </narration>
        
        <!-- 角色对话，包含姓名、标识符、情感和服装属性。
             除了name属性，所有的attribute都应该是英文。
             注意：详细介绍角色。 -->
        <character name="拉格娜" identifier="Wolfkin, 22 years old, female, blue eyes, gray fur, agile build" emotion="alert" clothes="leather armor, cloak">
            这些废墟古老而神秘。埃尔德里克，我们得小心点。我总感觉有双眼睛在暗处盯着我们，仿佛这片土地本身在注视着我们的每一步。
        </character>
        <character name="萨洛克" identifier="Orc, 35 years old, male, yellow eyes, green skin, muscular build" emotion="determined" clothes="warrior's garb, weapons">
            我们的任务是找到那隐藏的房间。这是揭开真相的唯一途径。保持警惕，我们离目标不远了。记住我们的训练，无论前路多么险恶，我们都能应对。
        </character>
        
        <!-- 继续通过环境描述增加紧张感。 -->
        <narration>
            随着他们一步步深入，空气愈发寒冷，阴影在他们周围悄然移动，仿佛有无形的力量在暗中窥探。风声在废墟间回荡，犹如鬼魅的低语，令人毛骨悚然。
        </narration>
        
        <!-- 确保角色情感与情境一致。 -->
        <character name="拉格娜" emotion="alert">
            你们听到了吗？我感觉到有东西在跟着我们……这地方真他妈的让人不寒而栗。
        </character>
        <character name="埃尔德里克" identifier="Human, 30 years old, male, brown eyes, fair skin, short black hair, average build" emotion="calm" clothes="scholar's robes">
            嗨，那只是风声，拉格娜。靠近些，我们会没事的。只要我们团结一致，就没有什么可怕的。
        </character>
        <character name="萨洛克" emotion="alert">
            不，拉格娜说得对。我也感觉到了。我们得小心，注意任何异常情况。
        </character>
        
        <!-- 引入神秘的声音以增加悬念。 -->
        <narration>
            突然，轻微的脚步声和低语在废墟中回荡，仿佛有幽灵在暗中徘徊。
        </narration>
        
        <!-- 角色对声音的反应，增加紧张感。 -->
        <character name="拉格娜" emotion="fearful">
            我去，那是什么？听起来像是从那堵墙后面传来的……我们得小心。
        </character>
        <character name="埃尔德里克" emotion="calm">
            走，我们去看看。小心点，待会会发生什么，谁也不知道。
        </character>
        <character name="萨洛克" emotion="determined">
            我先去瞧瞧，你们掩护我。
        </character>
        
        <!-- 发现隐藏通道，设置下一阶段。 -->
        <narration>
            萨洛克慢慢地推开一块石墙，露出了一条通向废墟更深处的隐藏通道，黑暗中仿佛有无数双眼睛在注视。
        </narration>
        
        <!-- 角色表达担忧，保持悬念。 -->
        <character name="拉格娜" emotion="alert">
            这条通道看起来很危险……你们确定要进去吗？
        </character>
        <character name="埃尔德里克" emotion="calm">
            哼，我们还有别的选择吗？这可能是我们唯一的机会。
        </character>
        <character name="拉格娜" emotion="fearful">
            他娘的……好吧，但我们必须非常小心。我总觉得这里有东西在盯着我们，让我心里发毛……
        </character>
        <character name="萨洛克" emotion="determined">
            别担心，拉格娜。我会在前面探路。你们跟在我后面。
        </character>
        
        <!-- 叙述描述他们通过通道的谨慎前进。 -->
        <narration>
            他们沿着狭窄的通道前行，每一步都小心翼翼。通道的尽头是一扇古老的木门，上面刻满了奇异的符文，仿佛在低声诉说着古老的咒语。
        </narration>
        
        <!-- 角色准备面对门后的未知。 -->
        <character name="埃尔德里克" emotion="calm">
            这些符文看起来像是古代的防护咒语。让我看看能不能破解它们……
        </character>
        <character name="拉格娜" emotion="alert">
            快点，埃尔德里克，我感觉到有什么东西在接近……
        </character>
        <character name="埃尔德里克" emotion="calm">
            别乌鸦嘴。我正在尽力，给我一点时间。
        </character>
        <character name="萨洛克" emotion="determined">
            我们必须保护埃尔德里克。拉格娜，注意周围的动静。
        </character>
        
        <!-- 通过接近的危险增加高潮。 -->
        <narration>
            就在这时，通道的另一端传来了沉重的脚步声，仿佛有什么庞大的生物正在靠近，空气中弥漫着一股压迫感。
        </narration>
        
        <!-- 角色对即将到来的威胁的反应。 -->
        <character name="拉格娜" emotion="fearful">
            草！我们得快点！那个东西越来越近了！
        </character>
        <character name="埃尔德里克" emotion="calm">
            我快破解了……再坚持一下！
        </character>
        <character name="萨洛克" emotion="determined">
            拉格娜，准备战斗。我们必须保护埃尔德里克！
        </character>
        
        <!-- 通过门打开解决即将到来的危险。 -->
        <narration>
            就在那千钧一发的瞬间，埃尔德里克的手指在古老符文上轻轻滑过，他的眼神集中，全神贯注。他的心跳在胸中砰砰作响，仿佛是在倒数计时。然后，就在那一刻，他成功破解了符文，那扇古老的门缓缓打开，仿佛是在欢迎他们的到来。门后是一个宽敞的房间，里面堆满了古老的文物和书籍。那些书籍被尘封的岁月覆盖，仿佛是在诉说着过去的故事。那些文物静静地躺在那里，仿佛是在等待着他们的发现。时间仿佛在这个房间里停滞，一切都显得那么静谧，那么神秘。
        </narration>
    </dialogue>
    
    <!-- 场景标签，定义新场景设置。
         注意：过渡到一个更安全但仍然神秘的环境。 -->
    <scene>
        <!-- 背景标签，使用关键词描述新场景的背景。
             除了name属性，所有的attribute都应该是英文。 
             注意："ancient library" 暗示了一个充满知识和秘密的地方。 -->
        <background keywords="ancient library, dimly lit, mysterious, dusty shelves, cobwebs, scattered scrolls"/>
        
        <!-- 音乐标签，使用关键词描述新的背景音乐。
             除了name属性，所有的attribute都应该是英文。
             注意：音乐现在应该更平静，但仍然保留一丝神秘感。 -->
        <music keywords="calm, mysterious, ambient, soft echoes, distant chimes, piano, 18th century"/>
    </scene>
    
    <!-- 在新场景中继续对话。
         除了name属性，所有的attribute都应该是英文。 
         注意：角色应反映他们的暂时安全并计划下一步。 -->
    <dialogue>
        <character name="埃尔德里克" emotion="hurry">
            我们进去了……快，进去，关上门！
        </character>
        <character name="拉格娜" emotion="relaxed">
            我们安全了吗？这太他妈吓人了。
        </character>
        <character name="萨洛克" emotion="determined">
            先休息一下，然后我们再决定下一步该怎么做。
        </character>
        
        <!-- 叙述暗示他们旅程的继续和即将到来的挑战。 -->
        <narration>
            他们终于在房间里找到了暂时的安全，但他们知道，这只是开始，真正的挑战还在前方……
        </narration>
    </dialogue>
    
    <!-- 选项标签，定义用户的多项选择。
         注意：提供有意义的选择，影响故事的发展方向。 -->
    <options>
        <!-- 多项选择部分的标题。
             注意：围绕主角的下一个行动框定选择。 -->
        <title>埃尔德里克接下来要怎么做？</title>
        
        <!-- 用户可以选择的每个选项。
             注意：确保选项多样化，并导致不同的结果。 -->
        <option>搜索废墟寻找线索</option>
        <option>探索隐藏的通道</option>
        <option>安营休息</option>
        <option>离开废墟重新集结</option>
    </options>
    
    <action>安营休息</action>
    
    <!-- 根据行动，续写新的scene、dialogue、options、action -->
</vnml>
```

**Note:** Apart from the `name` attribute, all other attributes should always be written in English.