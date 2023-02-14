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

import weakref as _weakref

from pyglet import clock as _clock
from pyglet import event as _event


class AnimationController(_event.EventDispatcher):

    _frame_index = 0
    _next_dt = 0
    _paused = False

    _animation = None

    def _animate(self, dt):
        raise NotImplementedError

    @property
    def paused(self) -> bool:
        """Pause/resume the Animation."""
        return self._paused

    @paused.setter
    def paused(self, pause):
        if not self._animation or pause == self._paused:
            return
        if pause is True:
            _clock.unschedule(self._animate)
        else:
            frame = self._animation.frames[self._frame_index]
            self._next_dt = frame.duration
            if self._next_dt:
                _clock.schedule_once(self._animate, self._next_dt)
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
