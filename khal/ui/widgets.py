# Copyright (c) 2013-2016 Christian Geier et al.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""A collection of (reusable) urwid widgets

Widgets that are specific to calendaring/khal should go into __init__.py or,
if they are large, into their own files
"""
from datetime import date, datetime, timedelta
import re

import urwid


class DateConversionError(Exception):
    pass


def delete_last_word(text, number=1):
    """delete last `number` of words from text"""
    words = re.findall(r"[\w]+|[^\w\s]", text, re.UNICODE)
    for one in range(1, number + 1):
        text = text.rstrip()
        if text == '':
            return text
        text = text[:len(text) - len(words[-one])]
    return text


def delete_till_beginning_of_line(text):
    """delete till beginning of line"""
    if text.rfind("\n") == -1:
        return ''
    return text[0:text.rfind("\n") + 1]


def delete_till_end_of_line(text):
    """delete till beginning of line"""
    if text.find("\n") == -1:
        return ''
    return text[text.find("\n"):]


def goto_beginning_of_line(text):
    if text.rfind("\n") == -1:
        return 0
    return text.rfind("\n") + 1


def goto_end_of_line(text):
    if text.find("\n") == -1:
        return len(text)
    return text.find("\n")


class ExtendedEdit(urwid.Edit):
    """A text editing widget supporting some more editing commands"""
    def keypress(self, size, key):
        if key == 'ctrl w':
            self._delete_word()
        elif key == 'ctrl u':
            self._delete_till_beginning_of_line()
        elif key == 'ctrl k':
            self._delete_till_end_of_line()
        elif key == 'ctrl a':
            self._goto_beginning_of_line()
        elif key == 'ctrl e':
            self._goto_end_of_line()
        else:
            return super(ExtendedEdit, self).keypress(size, key)

    def _delete_word(self):
        """delete word before cursor"""
        text = self.get_edit_text()
        f_text = delete_last_word(text[:self.edit_pos])
        self.set_edit_text(f_text + text[self.edit_pos:])
        self.set_edit_pos(len(f_text))

    def _delete_till_beginning_of_line(self):
        """delete till start of line before cursor"""
        text = self.get_edit_text()
        f_text = delete_till_beginning_of_line(text[:self.edit_pos])
        self.set_edit_text(f_text + text[self.edit_pos:])
        self.set_edit_pos(len(f_text))

    def _delete_till_end_of_line(self):
        """delete till end of line before cursor"""
        text = self.get_edit_text()
        f_text = delete_till_end_of_line(text[self.edit_pos:])
        self.set_edit_text(text[:self.edit_pos] + f_text)

    def _goto_beginning_of_line(self):
        text = self.get_edit_text()
        self.set_edit_pos(goto_beginning_of_line(text[:self.edit_pos]))

    def _goto_end_of_line(self):
        text = self.get_edit_text()
        self.set_edit_pos(goto_end_of_line(text[self.edit_pos:]) + self.edit_pos)


class EnterEdit(ExtendedEdit):
    """Edit class that emits signal `enter` if user tries to edit"""
    signals = ['enter']

    def keypress(self, size, key):
        if key not in ['up', 'down', 'left', 'right', 'tab', 'shift tab']:
            self._emit('enter')
            return
        else:
            return super().keypress(size, key)


class DateTimeWidget(ExtendedEdit):

    def __init__(self, dateformat, on_date_change=lambda x: None, **kwargs):
        self.dateformat = dateformat
        self.on_date_change = on_date_change
        super().__init__(wrap='any', **kwargs)

    def keypress(self, size, key):
        if key == 'ctrl x':
            self.decrease()
            return None
        elif key == 'ctrl a':
            self.increase()
            return None

        if (
                key in ['up', 'down', 'tab', 'shift tab'] or
                (key in ['right'] and self.edit_pos >= len(self.edit_text)) or
                (key in ['left'] and self.edit_pos == 0)):
            # when leaving the current Widget we check if currently
            # entered value is valid and if so pass the new value
            try:
                new_date = self._get_current_value()
            except DateConversionError:
                pass
            else:
                self.on_date_change(new_date)
        return super(DateTimeWidget, self).keypress(size, key)

    def increase(self):
        """call to increase the datefield by self.timedelta"""
        self._crease(self.dtype.__add__)

    def decrease(self):
        """call to decrease the datefield by self.timedelta"""
        self._crease(self.dtype.__sub__)

    def _crease(self, fun):
        """common implementation for `self.increase` and `self.decrease`"""
        try:
            new_date = fun(self._get_current_value(), self.timedelta)
            self.on_date_change(new_date)
            self.set_edit_text(new_date.strftime(self.dateformat))
        except DateConversionError:
            pass

    def set_value(self, new_date):
        """set a new value for this widget

        :type new_date: datetime.date
        """
        self.set_edit_text(new_date.strftime(self.dateformat))


class DateWidget(DateTimeWidget):
    dtype = date
    timedelta = timedelta(days=1)

    def _get_current_value(self):
        try:
            new_date = datetime.strptime(self.get_edit_text(), self.dateformat).date()
        except ValueError:
            raise DateConversionError
        else:
            return new_date


class TimeWidget(DateTimeWidget):
    dtype = datetime
    timedelta = timedelta(minutes=15)

    def _get_current_value(self):
        try:
            new_datetime = datetime.strptime(self.get_edit_text(), self.dateformat)
        except ValueError:
            raise DateConversionError
        else:
            return new_datetime


class Choice(urwid.PopUpLauncher):
    def __init__(self, choices, active, decorate_func=None, win_len=None):
        self.choices = choices
        self._win_len = win_len
        self._decorate = decorate_func or (lambda x: x)
        self.active = self._original = active

    def create_pop_up(self):
        pop_up = ChoiceList(self)
        urwid.connect_signal(pop_up, 'close', lambda button: self.close_pop_up())
        return pop_up

    @property
    def win_len(self):
        if self._win_len:
            return self._win_len
        else:
            return len(self.choices)

    def get_pop_up_parameters(self):
        return {'left': 0,
                'top': 1,
                'overlay_width': 32,
                'overlay_height': self.win_len}

    @property
    def changed(self):
        return self._active != self._original

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, val):
        self._active = val
        self.button = urwid.Button(self._decorate(self._active))
        urwid.PopUpLauncher.__init__(self, self.button)
        urwid.connect_signal(self.button, 'click',
                             lambda button: self.open_pop_up())


class EditSelect(Choice):
    def create_pop_up(self):
        pop_up = ChoiceListEdit(self)
        urwid.connect_signal(pop_up, 'close', lambda button: self.close_pop_up())
        return pop_up

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, val):
        self._active = val
        self.button = EnterEdit('', self._decorate(self._active))
        urwid.PopUpLauncher.__init__(self, self.button)
        urwid.connect_signal(self.button, 'enter', lambda button: self.open_pop_up())


class ChoiceList(urwid.WidgetWrap):
    signals = ['close']

    def __init__(self, parent):
        self.parent = parent
        buttons = []
        for c in parent.choices:
            buttons.append(
                urwid.Button(parent._decorate(c),
                             on_press=self.set_choice, user_data=c)
            )

        pile = NPile(buttons, outermost=True)
        fill = urwid.Filler(pile)
        urwid.WidgetWrap.__init__(self, urwid.AttrMap(fill, 'popupbg'))

    def set_choice(self, button, account):
        self.parent.active = account
        self._emit('close')

    def keypress(self, size, key):
        if key == 'esc':
            self._emit('close')
            return
        else:
            return super().keypress(size, key)


class ChoiceListEdit(ChoiceList):
    """
    +------------------+
    | Edit self._edit  |    Both Elements are wrapped in an NPile,
    +------------------+    one can jump from Edit to the Walker with tab
    | ListWalker       |    and back with shift tab
    | self._walker     |
    | over             |    When Edit is updated, only choices containing the
    | allowed          |    Edit.text are displayed
    | choices          |
    +------------------+
    """
    def __init__(self, parent):
        self.parent = parent
        self._edit = ExtendedEdit('', parent.active)
        urwid.connect_signal(self._edit, 'change',
                             lambda edit, text: self.filter(text))
        self._walker = urwid.SimpleFocusListWalker([self._edit])
        walker = urwid.BoxAdapter(
            urwid.ListBox(self._walker), height=self.parent.win_len - 1)
        self._pile = NPile([self._edit, walker], outermost=True)
        self.filter('')
        self.focus_on(self.parent.active)
        fill = urwid.Filler(self._pile, 'top')
        urwid.WidgetWrap.__init__(self, urwid.AttrMap(fill, 'popupbg'))

    def focus_on(self, text):
        for num, widget in enumerate(self._walker):
            if widget.label == text:
                self._walker.set_focus(num)
                return

    def filter(self, text):
        buttons = [self._edit]
        buttons = list()
        text = text.lower()
        for c in self.parent.choices:
            if text in c.lower():
                buttons.append(
                    urwid.Button(self.parent._decorate(c),
                                 on_press=self.set_choice, user_data=c)
                )

        if not buttons:
            buttons = [urwid.Text('no match')]
        pile = self._pile
        self._walker.clear()
        self._walker.extend(buttons)


class SupportsNext(object):
    """classes inheriting from SupportsNext must implement the following methods:
    _select_first_selectable
    _select_last_selectable
    """
    def __init__(self, *args, **kwargs):
        self.outermost = kwargs.get('outermost', False)
        if 'outermost' in kwargs:
            kwargs.pop('outermost')
        super(SupportsNext, self).__init__(*args, **kwargs)


class NextMixin(SupportsNext):
    """Implements SupportsNext for urwid.Pile and urwid.Columns"""
    def _select_first_selectable(self):
        """select our first selectable item (recursivly if that item SupportsNext)"""
        i = self._first_selectable()
        self.set_focus(i)
        if isinstance(self.contents[i][0], SupportsNext):
            self.contents[i][0]._select_first_selectable()

    def _select_last_selectable(self):
        """select our last selectable item (recursivly if that item SupportsNext)"""
        i = self._last_selectable()
        self.set_focus(i)
        if isinstance(self._contents[i][0], SupportsNext):
            self.contents[i][0]._select_last_selectable()

    def _first_selectable(self):
        """return sequence number of self.contents last selectable item"""
        for j in range(0, len(self._contents)):
            if self._contents[j][0].selectable():
                return j
        return False

    def _last_selectable(self):
        """return sequence number of self._contents last selectable item"""
        for j in range(len(self._contents) - 1, - 1, - 1):
            if self._contents[j][0].selectable():
                return j
        return False

    def keypress(self, size, key):
        key = super(NextMixin, self).keypress(size, key)

        if key == 'tab':
            if self.outermost and self.focus_position == self._last_selectable():
                self._select_first_selectable()
            else:
                for i in range(self.focus_position + 1, len(self._contents)):
                    if self._contents[i][0].selectable():
                        self.set_focus(i)
                        if isinstance(self._contents[i][0], SupportsNext):
                            self._contents[i][0]._select_first_selectable()
                        break
                else:  # no break
                    return key
        elif key == 'shift tab':
            if self.outermost and self.focus_position == self._first_selectable():
                self._select_last_selectable()
            else:
                for i in range(self.focus_position - 1, 0 - 1, -1):
                    if self._contents[i][0].selectable():
                        self.set_focus(i)
                        if isinstance(self._contents[i][0], SupportsNext):
                            self._contents[i][0]._select_last_selectable()
                        break
                else:  # no break
                    return key
        else:
            return key


class NPile(NextMixin, urwid.Pile):
    pass


class NColumns(NextMixin, urwid.Columns):
    pass


class NListBox(SupportsNext, urwid.ListBox):
    def _select_first_selectable(self):
        """select our first selectable item (recursivly if that item SupportsNext)"""
        i = self._first_selectable()
        self.set_focus(i)
        if isinstance(self.body[i], SupportsNext):
            self.body[i]._select_first_selectable()

    def _select_last_selectable(self):
        """select our last selectable item (recursivly if that item SupportsNext)"""
        i = self._last_selectable()
        self.set_focus(i)
        if isinstance(self.body[i], SupportsNext):
            self.body[i]._select_last_selectable()

    def _first_selectable(self):
        """return sequence number of self._contents last selectable item"""
        for j in range(0, len(self.body)):
            if self.body[j].selectable():
                return j
        return False

    def _last_selectable(self):
        """return sequence number of self.contents last selectable item"""
        for j in range(len(self.body) - 1, - 1, - 1):
            if self.body[j].selectable():
                return j
        return False

    def keypress(self, size, key):
        key = super().keypress(size, key)
        if key == 'tab':
            if self.outermost and self.focus_position == self._last_selectable():
                self._select_first_selectable()
            else:
                self._keypress_down(size)
        elif key == 'shift tab':
            if self.outermost and self.focus_position == self._first_selectable():
                self._select_last_selectable()
            else:
                self._keypress_up(size)
        else:
            return key


class ValidatedEdit(urwid.WidgetWrap):
    def __init__(self, *args, EditWidget=ExtendedEdit, validate=False, **kwargs):
        assert validate
        self._validate_func = validate
        self._original_widget = urwid.AttrMap(EditWidget(*args, **kwargs), 'edit', 'editf')
        super().__init__(self._original_widget)

    @property
    def _get_base_widget(self):
        return self._original_widget

    @property
    def base_widget(self):
        return self._original_widget.original_widget

    def _validate(self):
        text = self.base_widget.get_edit_text()
        if self._validate_func(text):
            self._original_widget.set_attr_map({None: 'edit'})
            self._original_widget.set_focus_map({None: 'edit'})
            return True
        else:
            self._original_widget.set_attr_map({None: 'alert'})
            self._original_widget.set_focus_map({None: 'alert'})
            return False

    def get_edit_text(self):
        self._validate()
        return self.base_widget.get_edit_text()

    @property
    def edit_pos(self):
        return self.base_widget.edit_pos

    @property
    def edit_text(self):
        return self.base_widget.edit_text

    def keypress(self, size, key):
        if (
                key in ['up', 'down', 'tab', 'shift tab'] or
                (key in ['right'] and self.edit_pos >= len(self.edit_text)) or
                (key in ['left'] and self.edit_pos == 0)):
            if not self._validate():
                return
        return super().keypress(size, key)
