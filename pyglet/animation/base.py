# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2022 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

"""Animations

Animations can be used by the :py:class:`~pyglet.sprite.Sprite` class in place
of static images. They are essentially containers for individual image frames,
with a duration per frame. They can be infinitely looping, or stop at the last
frame. You can load Animations from disk, such as from GIF files::

    ani = pyglet.resource.animation('walking.gif')
    sprite = pyglet.sprite.Sprite(img=ani)

Alternatively, you can create your own Animations from a sequence of images
by using the :py:meth:`~Animation.from_image_sequence` method::

    images = [pyglet.resource.image('walk_a.png'),
              pyglet.resource.image('walk_b.png'),
              pyglet.resource.image('walk_c.png')]

    ani = pyglet.image.Animation.from_image_sequence(images, duration=0.1, loop=True)

You can also use an :py:class:`pyglet.image.ImageGrid`, which is iterable::

    sprite_sheet = pyglet.resource.image('my_sprite_sheet.png')
    image_grid = pyglet.image.ImageGrid(sprite_sheet, rows=1, columns=5)

    ani = pyglet.image.Animation.from_image_sequence(image_grid, duration=0.1)

In the above examples, all the Animation Frames have the same duration.
If you wish to adjust this, you can manually create the Animation from a list of
:py:class:`~AnimationFrame`::

    image_a = pyglet.resource.image('walk_a.png')
    image_b = pyglet.resource.image('walk_b.png')
    image_c = pyglet.resource.image('walk_c.png')

    frame_a = AnimationFrame(image_a, duration=0.1)
    frame_b = AnimationFrame(image_b, duration=0.2)
    frame_c = AnimationFrame(image_c, duration=0.1)

    ani = pyglet.image.Animation(frames=[frame_a, frame_b, frame_c])

"""

import weakref

from pyglet import clock
from pyglet import event


class AnimationController(event.EventDispatcher):

    _frame_index = 0
    _next_dt = 0
    _paused = False

    def __init__(self, animation, function):
        self._animation = animation
        self._function = weakref.proxy(function)

    def _animate(self, dt):
        self._frame_index += 1
        if self._frame_index >= len(self._animation.frames):
            self._frame_index = 0
            self.dispatch_event('on_animation_end')

        frame = self._animation.frames[self._frame_index]
        self._function(frame)

        if frame.duration is not None:
            duration = frame.duration - (self._next_dt - dt)
            duration = min(max(0, duration), frame.duration)
            clock.schedule_once(self._animate, duration)
            self._next_dt = duration
        else:
            self.dispatch_event('on_animation_end')

    @property
    def paused(self) -> bool:
        """Pause/resume the Animation."""
        return self._paused

    @paused.setter
    def paused(self, pause):
        if not self._animation or pause == self._paused:
            return
        if pause is True:
            clock.unschedule(self._animate)
        else:
            frame = self._animation.frames[self._frame_index]
            self._next_dt = frame.duration
            if self._next_dt:
                clock.schedule_once(self._animate, self._next_dt)
        self._paused = pause

    @property
    def frame_index(self) -> int:
        """The current AnimationFrame."""
        return self._frame_index

    @frame_index.setter
    def frame_index(self, index):
        # Bound to available number of frames
        if self._animation is None:
            return
        self._frame_index = max(0, min(index, len(self._animation.frames)-1))


AnimationController.register_event_type('on_animation_end')


class Animation:
    """Sequence of frames with timing information.

    If no frames of the animation have a duration of ``None``, the animation
    loops continuously; otherwise the animation stops at the first frame with
    duration of ``None``.

    :Ivariables:
        `frames` : list of `~pyglet.animation.AnimationFrame`
            The frames that make up the animation.

    """

    def __init__(self, frames: list):
        """Create an animation directly from a list of frames."""
        assert len(frames)
        self.frames = frames

    def get_duration(self) -> float:
        """Get the total duration of the animation in seconds."""
        return sum([frame.duration for frame in self.frames if frame.duration is not None])

    @classmethod
    def from_sequence(cls, sequence: list, duration: float, loop: bool = True):
        """Create an animation from a list of objects and a constant framerate."""
        frames = [AnimationFrame(image, duration) for image in sequence]
        if not loop:
            frames[-1].duration = None
        return cls(frames)

    def __repr__(self):
        return "Animation(frames={0})".format(len(self.frames))


class AnimationFrame:
    """A single frame of an animation."""

    __slots__ = 'data', 'duration'

    def __init__(self, data, duration):
        self.data = data
        self.duration = duration

    def __repr__(self):
        return "AnimationFrame({0}, duration={1})".format(self.data, self.duration)
