### VNML Syntax Documentation

VNML (Visual Novel Markup Language) is designed to construct and manage interactive visual novel narratives. This
document details the syntax and fields of VNML, accompanied by examples.

### Syntax Overview

#### `<setup>`

The `<setup>` section defines the initial setup of the visual novel, including character personalities, story
background, and objectives. Characters are divided into NPCs (non-player characters) and the player.

##### Fields:

- **`<story>`**: Contains the story background and objectives.
    - **`<background>`**: Describes the background setting of the story.
    - **`<objective>`**: Describes the main objective or goal of the story.

- **`<npcs>`**: Contains the definitions of each non-player character.
    - **`<npc>`**: Defines a non-player character.
        - **`name`**: The name of the character.
        - **`identifier`**: Describes the character's basic information such as age, gender, and physical traits (
          excluding clothing and accessories).
        - **`habits`**: Describes the character's typical behaviors and habits.
        - **`core-traits`**: Describes the core traits of the character's personality.
        - **`self-perception`**: Describes how the character perceives themselves.
        - **`dark-side`**: Describes the character's negative traits or hidden side.

- **`<player>`**: Defines the player character.
    - **`name`**: The name of the player character.
    - **`identifier`**: Describes the character's basic information such as age, gender, and physical traits (excluding
      clothing and accessories).
    - **`habits`**: Describes the character's typical behaviors and habits.
    - **`core-traits`**: Describes the core traits of the character's personality.
    - **`self-perception`**: Describes how the character perceives themselves.
    - **`dark-side`**: Describes the character's negative traits or hidden side.

- **`<relationships>`**: Defines the relationships between characters.
    - **`<relationship>`**: Describes a relationship between two characters.
        - **`category`**: The category of the relationship, which can be either:
            - **`formal`**: Represents explicit, socially recognized relationships (e.g., friends, family, colleagues).
            - **`hidden`**: Represents implicit, unspoken relationships (e.g., secret crushes, past affairs).
        - **`type`**: The type of relationship (e.g., friend, love).
        - **`from`**: The character from whom the relationship originates.
        - **`to`**: The character to whom the relationship is directed.
        - **`description`**: A description of the relationship.

#### `<player-input>`

The `<player-input>` section defines player commands or inputs.

##### Fields:

- **`<command>`**: The command or input taken by the user.

#### `<ai-response>`

The `<ai-response>` section defines the AI's response to user input, including scene settings, scripts, user inventory,
and multiple-choice options.

##### Fields:

- **`<scene>`**: Defines the initial scene settings.
    - **`<background>`**: Describes the background scene using keywords.
        - **`keywords`**: A comma-separated list of keywords describing the background (e.g., "stormy night, abandoned
          mansion").
    - **`<music>`**: Describes the background music using keywords.
        - **`keywords`**: A comma-separated list of keywords describing the music (e.g., "tense, orchestral, eerie").

- **`<dialogue>`**: Contains mixed narration and dialogue. Should exceed 50 lines.
    - **`<narration>`**: Describes the narration text.
    - **`<npc>`**: Describes the dialogue text and clothes of the NPC.
        - **`name`**: The name of the character speaking.
        - **`emotion`**: The emotion of the character while speaking (if different from the previous dialogue).
        - **`clothes`**: A comma-separated list of items describing the character's clothing and accessories (if
          different from the previous dialogue).
    - **`<player>`**: Describes the dialogue text and clothes of the Player.
        - **`name`**: The name of the character speaking.
        - **`emotion`**: The emotion of the character while speaking (if different from the previous dialogue).
        - **`clothes`**: A comma-separated list of items describing the character's clothing and accessories (if
          different from the previous dialogue).
    - **`<passerby>`**: Describes a one-time character appearing in the dialogue.
        - **`name`**: The name of the passerby character.
        - **`identifier`**: Describes the character's basic information such as age, gender, and physical traits (
          excluding clothing and accessories).
        - **`emotion`**: The emotion of the character while speaking (if different from the previous dialogue).
        - **`clothes`**: A comma-separated list of items describing the character's clothing and accessories (if
          different from the previous dialogue).
    - **`<sound-effect>`**: Describes sound-effect effects in the script.
        - **`keywords`**: A comma-separated list of keywords describing the sound-effect effect (e.g., "thunder,
          creaking, footsteps").
        - **`duration`**: Duration of the sound-effect effect in seconds (e.g., "3s").

- **`<options>`**: Defines the user's multiple-choice options.
    - **`<title>`**: The title of the multiple-choice section.
    - **`<option>`**: Each option that the user can choose.
        - **`text`**: The text of the option.

In VNML, comments serve as a versatile tool for developers. They can be utilized as a scratchpad for jotting down
thoughts, planning code structure, storing hints for future reference, and more.

### Example

```xml

<vnml version="1">
    <!-- Establishing the initial setting and characters for the story -->
    <setup>
        <story>
            <background>Deep within the forest lies a hidden ruin, rumored to hold ancient secrets.</background>
            <objective>Uncover the truth behind the ruins and unlock their mysteries.</objective>
        </story>
        <npcs>
            <!-- Tharok: A character with a strong sense of duty and honor, but with a hidden envy for Eldric's abilities -->
            <npc name="Tharok">
                <identifier>Orc, 35 years old, male, yellow eyes, green skin, muscular build</identifier>
                <habits>Enjoys crafting weapons, often seen training in combat</habits>
                <core-traits>Strong, honorable, stoic</core-traits>
                <self-perception>Sees himself as a protector of his tribe</self-perception>
                <dark-side>Can be ruthless and uncompromising</dark-side>
            </npc>
            <!-- Ragna: A vigilant and loyal scout, with a secret fear of Tharok's ruthlessness -->
            <npc name="Ragna">
                <identifier>Wolfkin, 22 years old, female, blue eyes, gray fur, agile build</identifier>
                <habits>Frequently scouts the surroundings, enjoys hunting</habits>
                <core-traits>Alert, loyal, cunning</core-traits>
                <self-perception>Sees herself as the eyes and ears of the team</self-perception>
                <dark-side>Can be distrustful and secretive</dark-side>
            </npc>
        </npcs>
        <!-- Eldric: The player character, a seeker of knowledge with a cautious nature -->
        <player name="Eldric">
            <identifier>Human, 30 years old, male, brown eyes, fair skin, short black hair, average build</identifier>
            <habits>Enjoys studying ancient texts, has a passion for magic</habits>
            <core-traits>Wise, curious, compassionate</core-traits>
            <self-perception>Sees himself as a seeker of knowledge</self-perception>
            <dark-side>Can be overly cautious and skeptical</dark-side>
        </player>
        <!-- Establishing complex relationships among characters to add depth to the narrative -->
        <relationships>
            <relationship category="formal" type="friend" from="Eldric" to="Tharok">Eldric and Tharok have a mutual
                respect forged in battle
            </relationship>
            <relationship category="hidden" type="envy" from="Tharok" to="Eldric">Tharok envies Eldric's magical
                abilities and knowledge
            </relationship>
            <relationship category="hidden" type="fear" from="Ragna" to="Tharok">Ragna secretly fears Tharok's
                ruthlessness
            </relationship>
            <relationship category="hidden" type="resentment" from="Tharok" to="Ragna">Tharok resents Ragna's
                distrustful nature
            </relationship>
            <relationship category="hidden" type="guilt" from="Eldric" to="Ragna">Eldric feels guilty for a past
                incident that endangered Ragna
            </relationship>
        </relationships>
    </setup>

    <!-- The player's action to drive the story forward -->
    <player-input>
        <command>Investigate the ruins</command>
    </player-input>

    <!-- The AI's response to the player's action, advancing the plot -->
    <ai-response>
        <!-- Setting the scene to create an immersive atmosphere -->
        <scene>
            <background keywords="ancient ruins, dense forest, twilight"/>
            <music keywords="mystical, ambient, suspenseful"/>
        </scene>

        <!-- Dialogue and narration to build tension and develop characters, more than 50 lines, clothes of the same character appears only once if not changed -->
        <dialogue>
            <narration>The sun was setting as Eldric, Tharok, and Ragna approached the ancient ruins hidden deep within
                the forest.
            </narration>
            <npc name="Ragna" emotion="alert" clothes="leather armor, hunting knife">These ruins are old. We should be
                careful, Eldric.
            </npc>
            <npc name="Ragna">I can sense something watching us.</npc>
            <npc name="Tharok" emotion="determined" clothes="iron armor, battle axe">We need to find the hidden chamber.
                It's the only way to uncover the truth.
            </npc>
            <npc name="Tharok">Stay focused. We're close to finding it.</npc>
            <npc name="Tharok" emotion="serious">Remember our training. We can handle whatever comes our way.</npc>
            <npc name="Tharok">We've faced worse dangers before. This is just another challenge.</npc>
            <npc name="Tharok" emotion="determined">Keep your guard up and stay vigilant.</npc>
            <npc name="Tharok">We must be prepared for anything.</npc>
            <sound-effect keywords="rustling leaves, distant howl" duration="3s"/>
            <narration>As they ventured deeper into the ruins, the air grew colder, and the shadows seemed to shift
                around them.
            </narration>
            <npc name="Ragna" emotion="nervous">Did you hear that? I think something is following us.</npc>
            <npc name="Ragna">This place is giving me chills.</npc>
            <player name="Eldric" emotion="calm" clothes="wizard's robe, staff">It's just the wind, Ragna. Stay close to
                us.
            </player>
            <player name="Eldric">We'll be fine as long as we stick together.</player>
            <npc name="Tharok" emotion="alert">No, Ragna's right. I sense it too. We need to be cautious.</npc>
            <npc name="Tharok">Keep your eyes open for anything unusual.</npc>
            <npc name="Ragna" emotion="curious">But what if it's something more than just the wind?</npc>
            <npc name="Ragna">I've read about places like this. They often have hidden dangers.</npc>
            <npc name="Ragna" emotion="nervous">And sometimes, those dangers are better left undisturbed.</npc>
            <player name="Eldric" emotion="determined">That's exactly why we're here, Ragna. To uncover the truth, no
                matter how perilous it might be.
            </player>
            <player name="Eldric">We can't turn back now.</player>
            <npc name="Tharok" emotion="supportive">Eldric is right. We've faced worse before. We can handle this.</npc>
            <npc name="Tharok">Just stay close and trust us.</npc>
            <npc name="Tharok">We need to stay united and strong.</npc>
            <npc name="Tharok" emotion="excited">Together, we can overcome any obstacle.</npc>
            <npc name="Tharok">Let's move forward with confidence.</npc>
            <sound-effect keywords="footsteps, whispering" duration="4s"/>
            <narration>Suddenly, they heard faint whispering and footsteps echoing through the ruins.</narration>
            <npc name="Ragna" emotion="terrified">What was that? It sounded like it came from behind that wall.</npc>
            <npc name="Ragna">We should be careful.</npc>
            <player name="Eldric" emotion="calm">Let's check it out. Stay close and be ready for anything.</player>
            <player name="Eldric">We need to be cautious.</player>
            <npc name="Tharok" emotion="alert">I'll go first. Cover me.</npc>
            <npc name="Tharok">Be prepared for anything.</npc>
            <npc name="Tharok" emotion="determined">We must be ready for whatever lies ahead.</npc>
            <npc name="Tharok">Stay alert and focused.</npc>
            <npc name="Tharok">This could be the key to our mission.</npc>
            <sound-effect keywords="stone grinding" duration="3s"/>
            <narration>Tharok slowly pushed against the wall, revealing a hidden passageway leading further into the
                ruins.
            </narration>
            <!-- Introducing a passerby character -->
            <passerby name="Mysterious Figure" identifier="Unknown, cloaked, indistinguishable features"
                      emotion="mysterious" clothes="dark cloak, hood">
                Beware, travelers. The path ahead is fraught with peril.
            </passerby>
            <npc name="Eldric" emotion="curious">Who are you? And why are you warning us?</npc>
            <passerby name="Mysterious Figure">I am but a shadow, a remnant of those who came before. Heed my warning,
                or face the consequences.
            </passerby>
            <npc name="Tharok" emotion="determined">We appreciate your warning, but we must proceed. Our mission is too
                important.
            </npc>
            <passerby name="Mysterious Figure">Then may fate be kind to you. Farewell.</passerby>
            <sound-effect keywords="rustling cloak, footsteps fading" duration="3s"/>
            <narration>The mysterious figure disappeared into the shadows, leaving the group with an uneasy feeling.
            </narration>
        </dialogue>

        <!-- Offering choices to the player to influence the story's direction -->
        <options title="What should Eldric do next?">
            <option text="Search the ruins for clues"/>
            <option text="Explore the hidden passageway"/>
            <option text="Set up camp and rest"/>
            <option text="Leave the ruins and regroup"/>
        </options>
    </ai-response>

    <!-- The player's decision to drive the narrative forward -->
    <player-input>
        <command>Explore the hidden passageway</command>
    </player-input>

    <!-- The AI's response to the player's choice, continuing the plot's progression -->
    <ai-response>
        <!-- Creating an eerie atmosphere as they venture deeper into the ruins -->
        <scene>
            <background keywords="dark passageway, ancient carvings, eerie glow"/>
            <music keywords="mysterious, suspenseful, quiet"/>
        </scene>

        <!-- Dialogue and narration to build tension and develop characters, more than 50 lines, clothes of the same character appears only once if not changed -->
        <dialogue>
            <narration>They entered the dark passageway, the walls adorned with ancient carvings that seemed to glow
                faintly.
            </narration>
            <npc name="Ragna" emotion="curious">These carvings... they tell a story. Something important must be hidden
                here.
            </npc>
            <npc name="Ragna">We need to decipher them.</npc>
            <player name="Eldric" emotion="focused">Look for anything that might hint at the hidden chamber. Symbols,
                patterns, anything unusual.
            </player>
            <player name="Eldric">We need to find clues quickly.</player>
            <player name="Eldric">These carvings might hold the key to understanding the ruins.</player>
            <player name="Eldric">Pay close attention to every detail.</player>
            <player name="Eldric">We can't afford to miss anything important.</player>
            <player name="Eldric">Time is of the essence. Let's move.</player>
            <sound-effect keywords="pages rustling, thud" duration="2s"/>
            <npc name="Tharok" emotion="tense">Did you hear that? It sounded like it came from deeper within the
                passage.
            </npc>
            <npc name="Tharok">We should check it out.</npc>
            <npc name="Tharok">Stay alert, there might be traps.</npc>
            <npc name="Tharok">We need to be cautious.</npc>
            <npc name="Tharok">Let's proceed carefully.</npc>
            <npc name="Tharok">We can't afford any mistakes.</npc>
            <sound-effect keywords="stone grinding, secret door" duration="3s"/>
            <narration>With a creak, a section of the wall slid aside, revealing a hidden chamber filled with ancient
                artifacts.
            </narration>
            <npc name="Ragna" emotion="anxious">Are we really going in there?</npc>
            <npc name="Ragna">It looks dangerous.</npc>
            <player name="Eldric" emotion="determined">Yes, we are. This might be the key to uncovering the secrets of
                the ruins.
            </player>
            <player name="Eldric">We have to take the risk.</player>
            <npc name="Tharok" emotion="resolute">Eldric's right. We've come too far to turn back now.</npc>
            <npc name="Tharok">Let's proceed, but stay on guard.</npc>
            <narration>As they stepped into the hidden chamber, the air grew colder, and an eerie silence enveloped
                them.
            </narration>
            <npc name="Ragna" emotion="nervous">I don't like this. Something feels off.</npc>
            <npc name="Ragna">We need to be very careful.</npc>
            <player name="Eldric" emotion="focused">Let's search the room. Look for anything that might give us a clue
                about the ruins' secrets.
            </player>
            <player name="Eldric">We need to be thorough in our search.</player>
            <sound-effect keywords="footsteps, echoing" duration="4s"/>
            <narration>They spread out, examining the ancient artifacts and inscriptions that covered the walls.
            </narration>
            <npc name="Tharok" emotion="curious">These symbols... they look familiar. I've seen them in old texts.</npc>
            <npc name="Tharok">They might be related to the ancient guardians of this place.</npc>
            <npc name="Ragna" emotion="excited">Look here, Eldric! This artifact... it seems to be a key of some sort.
            </npc>
            <npc name="Ragna">It might unlock a hidden mechanism.</npc>
            <player name="Eldric" emotion="interested">Good find, Ragna. Let's see if we can use it to reveal more
                secrets.
            </player>
            <player name="Eldric">This might be the breakthrough we need.</player>
            <sound-effect keywords="clicking, mechanism activating" duration="3s"/>
            <narration>As Eldric placed the artifact into a slot in the wall, a hidden door slowly opened, revealing a
                staircase leading further down.
            </narration>
            <npc name="Tharok" emotion="determined">This is it. We need to go deeper.</npc>
            <npc name="Tharok">Stay close and be ready for anything.</npc>
            <npc name="Ragna" emotion="anxious">I hope we're not walking into a trap.</npc>
            <npc name="Ragna">But we have no choice but to proceed.</npc>
            <player name="Eldric" emotion="resolute">Let's move. We need to uncover the truth, no matter the cost.
            </player>
            <player name="Eldric">We're in this together.</player>
            <sound-effect keywords="footsteps, descending stairs" duration="5s"/>
            <narration>They descended the staircase, their footsteps echoing through the ancient stone corridor.
            </narration>
            <npc name="Tharok" emotion="alert">Keep your eyes open. We don't know what lies ahead.</npc>
            <npc name="Tharok">We need to be prepared for anything.</npc>
            <npc name="Ragna" emotion="nervous">I have a bad feeling about this.</npc>
            <npc name="Ragna">But we must press on.</npc>
            <player name="Eldric" emotion="determined">We're close to uncovering the truth. Let's keep moving.</player>
            <sound-effect keywords="distant chanting, eerie" duration="4s"/>
            <narration>As they reached the bottom of the staircase, they heard distant chanting, growing louder with
                each step.
            </narration>
            <npc name="Tharok" emotion="tense">Do you hear that? It sounds like chanting.</npc>
            <npc name="Tharok">We need to be careful.</npc>
            <npc name="Ragna" emotion="fearful">This can't be good. We should be ready for anything.</npc>
            <player name="Eldric" emotion="focused">Let's proceed with caution. We need to find out what's happening
                here.
            </player>
            <sound-effect keywords="chanting, increasing volume" duration="5s"/>
            <narration>They followed the sound of chanting, which led them to a large, dimly lit chamber filled with
                ancient relics and symbols.
            </narration>
            <npc name="Tharok" emotion="alert">This must be the heart of the ruins. Be on guard.</npc>
            <npc name="Ragna" emotion="anxious">What is this place? It feels... powerful.</npc>
            <player name="Eldric" emotion="determined">This is it. The answers we seek must be here. Let's find them.
            </player>
        </dialogue>

        <!-- Offering new choices to the player to influence the story's direction -->
        <options title="What should Eldric do next?">
            <option text="Investigate the chanting"/>
            <option text="Examine the ancient relics"/>
            <option text="Search for hidden passages"/>
            <option text="Prepare for a potential confrontation"/>
        </options>
    </ai-response>
</vnml>
```