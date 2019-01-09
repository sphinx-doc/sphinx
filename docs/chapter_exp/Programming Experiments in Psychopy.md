# Where we are coming from, and where we are

## Story Time: Galton's Pendulum

In the 1880s, scientific progress had opened up a novel option for the
citizens of Her Majesty Queen Victoria to entertain themselves with:
have their psychometric traits measured
in Francis Galton's *Science Galleries*, at the South Kensington Museum.
Visitors paid "3 pence" (presumably some sort of currency), and then had their
mental traits measured. Thousands of participants volunteered, establishing
one of the first large-sample psychometric databases. Amongst the things
measured was how long it took the curious museum goer to press a button in
response to a simple light stimulus.

Galton measured response times using an ingenious design called the ["pendulum
chronograph"](http://galton.org/essays/1880-1889/galton-1889-rba-reaction-time.pdf).
Its intricate mechanism -- the position of the pendulum when the key was pushed
could be compared to a table, giving an estimate of response time --
had a then-state of the art resolution of 1/100th of a second.

![Some of Galton's tools. The pendulum chronograph is more complicated than any
of these! Public domain image taken from @johnson1985galton.
](figures/galtons_instruments.png)

Other experimenters around this time were stopping response latencies with
manual stopwatches.
Galton himself conducted human geographic surveys by walking around London,
mentally rating the women he saw for their attractiveness, and covertly noting
the ratings with a selfmade device: a paper cross, into which he, in his pocket,
punched a hole indicating if the woman was of below average, average, or above
average "beauty".

It is not advised to mention such practices in a contemporary presentation of
scientific results. At the very least, the practices would be seen as grossly
inaccurate, and for many, highly open to experimenter bias. In particular, they
lack precision. Also, to be frank -- they sound like a lot
of work! While some might decry a lack of entrepeneurial spirit, most of us will
readily admit the advantage of computerized methods.

Progress has made the work of the researcher much simpler. (Remember this
sentence whenever you feel frustrated attempting to program an experiment!
At least you are not Galton, keeping a pendulum chronograph in working
condition, or walking across London to mentally file people into rather crude
and subjective boxes.)
Today, computers can show all kinds of visual input, play all kinds of sounds,
and accurately measure ... well, a narrow kind of behavioral responses by
study participants. The computer's graphics and sound cards, and the keyboard
and mouse drivers, are relatively arcane. There is as of yet no convenient
way to get a computer to show words or pictures on a screen for the purposes
of psychological experiments from our favourite programming language, R.
There are many commercial, closed-source solutions, which we will all ignore in
favour of the powerful and open Python options.

Why? Perhaps the most important benefit computerized experiments have is that they
are much more reproducible.
Using an Open Source program and making experimental stimuli
and scripts available online allows other researchers to 1. exactly retrace
what happened in the original experiment, 2. repeat it ad libitum.
To actually exploit this reproducibility potential, we must use software that is
open. The biggest open source experimental presentation software is Psychopy
[@peirce2007psychopy].

## Programming Experiments in Python with Psychopy

Psychopy allows us to write simple and readable Python code to control our
computer's low-level capacity for displaying and playing stimuli. Why is this
necessary? Because we need to work with the computer on a low level in order to
get it to achieve highly precise timings, and smoothly display even complex
visual stimuli. That is one half of the experimental program; the other will 
consist in translating the [experimental design](experimental_design) into
computer code, so that, e.g., a study participant is presented with the required
number of trials resulting from your [power calculation](power) for the
conditions resulting from your [latin square design](experimental_design).

Because Psychopy is written in Python, we having already learned Python,
learning Psychopy reduces to learning the Psychopy-specific modules.


### The basic logic of experiments in Psychopy

#### Stimuli

Psychopy can display auditory and visual stimuli; visual stimuli may be static,
or dynamic (moving animations, or videos). To display visual stimuli, Psychopy
must know about at least one `Monitor`, and at least one `Window`. Such a
`Window` is the plane on which drawn stimuli will be shown. Note that `Monitor`
and `Window` are software objects primarily inside of Psychopy. They
allow Psychopy to show things in a window on your physical screen
(or fullscreen).

Internally, Psychopy knows the backside and the front side of each `Window`.
When a `Window` is newly created, both sides will be empty. We can now
draw things on the backside (using the `draw` method of various visual
objects). Once everything we want to show has been drawn, the `Window` is
"flipped" so that the painted backside is now shown on the physical screen.
The new backside is blank. We can now draw other things on this blank backside.
One option might be to draw nothing, to show a blank screen after the current
stimulus.
Eventually, we flip again; this clears everything we had drawn on the original
backside, and shows the other side on the screen. So: we manually paint --
piece by piece -- one side of the window with everything we want to show, flip
it to show it, paint the new backside, flip again to show and clear, and repeat.

The visual stimuli we can paint on screens live in the `psychopy.visual`
submodule. This includes various geometric shapes, as well as the `TextStim`
and `ImageStim` classes, which we will discuss extensively in the following. 

For movie stimuli, see the [MovieStim](http://www.psychopy.org/api/visual/moviestim.html)
class. Other stimuli include random dot motion and grating stimuli.

#### Keeping track of time and responses

Psychopy allows collecting button or keyboard responses and mouse events.

#### Accuracy and Precision

In principle, Psychopy can be highly accurate. In practice, much depends on
specifics of the experiment and context [@garaizar2014accuracy; @Plant2016].
Consider: one study has reported that Galton observed slightly *faster*
response times in Victorian times than are observed in contemporary experiments
[@woodley2013were]. Could it be that the Victorians were mentally faster than
us? An alternative suggestion for this has been that timings on digital devices
are only ever approximations; [i.e., many digital devices could not record
increments shorter than 100 ms!](http://deevybee.blogspot.com/2013/05/have-we-become-slower-and-dumber.html)
Even with modern computer technology, the accuracy of stimulus presentation
timing is never better than the screen refresh rate. For example, many laptop
monitors have refresh rates of 60 Hz. That is, they can at most show a new
stimulus 16.5 ms after the previous stimulus, and all stimulus 
timing intervals will *at best* be multiples of 16.5.

Remember the distinction between accuracy and precision: some of the inaccuracy
of stimulus and response time collection will be random jitter. In many cases,
this will simply show up as noise in the data (and thus, decrease the power of
the experiment). Systematic distortions are not a necessary consequence
[@Vadillo2016]. But other aspects represent an
inherent bias. For example, for build-in sound cards, auditory stimulus
presentation onset is preceded by a delay. Typically, this delay will be
approximately the same on every trial; but it will lead to a systematic
underestimation of stimulus onsets.

For experiments requiring extremely precise measurements, it becomes crucial to 
measure, minimize and account for inaccuracy and bias. For this, external
hardware is required; i.e., light- or sound pressure sensitive detectors.
(For a cheap solution, the Raspberry Pi mini-computer can easily be
extended for this purpose.)

## Alternative software

### OpenSesame

[@mathot2012opensesame]

### Going online: surveys on the internet

#### Online Experiments with the Psychopy Builder

#### JsPsych

#### Mechanical Turk
