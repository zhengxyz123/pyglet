# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2019 Alex Holkner
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
from pyglet.gl import GLuint, glGenVertexArrays, glDeleteVertexArrays, glBindVertexArray


class VertexArray:
    """OpenGL Vertex Array Object"""

    def __init__(self):
        """Create an instance of a Vertex Array object."""
        self._id = GLuint()
        glGenVertexArrays(1, self._id)

    @property
    def id(self):
        return self._id.value

    def bind(self):
        glBindVertexArray(self._id)

    @staticmethod
    def unbind():
        glBindVertexArray(0)

    def delete(self):
        glDeleteVertexArrays(1, self._id)

    __enter__ = bind

    __exit__ = unbind

    def __del__(self):
        try:
            glDeleteVertexArrays(1, self._id)
        # Python interpreter is shutting down:
        except ImportError:
            pass

    def __repr__(self):
        return "{0}(id={1})".format(self.__class__.__name__, self._id.value)
