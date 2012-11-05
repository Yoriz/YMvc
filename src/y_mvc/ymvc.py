'''
Created on 25 Oct 2012

@author: Dave Wilson
'''

from uuid import uuid4


class Observer(object):
    '''Stores a dictionary of functions that will be notified if they
    have an interest in a event_name'''
    def __init__(self):
        self.observers = {}

    def register(self, event_name, func, uid):
        '''Register a function/uid pair's interest in a event_name'''
        if not event_name in self.observers:
            self.observers[event_name] = {}
        self.observers[event_name][uid] = func

    def notify(self, event_name, data="", uid="", **kwargs):
        '''notify any functions interested in event_name'''
        note = {"event_name": event_name, "data": data, "uid": uid}
        note.update(kwargs)
        observer_dict = self.observers.get(event_name, False)
        if observer_dict:
            for func in observer_dict.itervalues():
                func(note)

    def unregister(self, event_name, uid):
        '''unregister uid's interest in event_name'''
        self.observers[event_name].pop(uid, None)
        if not self.observers[event_name]:
            self.observers.pop(event_name, None)


class UniqueDict(dict):
    '''Dict that errors if you don't have your key values under control'''
    def __setitem__(self, key, value):
        '''Raises error if you set a key value that already has some value'''
        if key in self:
            raise KeyError("Item named %s already exists" % key)
        return dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        '''Raises error if you try to get a non existant key'''
        if not key in self:
            raise KeyError("Item named %s not found" % key)
        return dict.__getitem__(self, key)

    def __delitem__(self, key):
        '''Raised an error if you try to delete a non existant key'''
        if not key in self:
            raise KeyError("Item named %s not found" % key)
        return dict.__delitem__(self, key)


class ObjectStore(object):
    ''''''
    def __init__(self):
        ''''''
        self.unique_dict = UniqueDict()

    def has_object(self, obj_name):
        ''''''
        return obj_name in self.unique_dict

    def register_object(self, obj_name, obj):
        ''''''
        self.unique_dict[obj_name] = obj
        obj.on_register()
        return obj

    def retrieve_object(self, obj_name):
        ''''''
        return self.unique_dict[obj_name]

    def remove_object(self, obj_name):
        ''''''
        obj = self.unique_dict[obj_name]
        del self.unique_dict[obj_name]
        obj.on_remove()
        return obj


class EventHandler(object):
    def __init__(self, observer):
        self.uid = uuid4()
        self.events = UniqueDict()
        self.observer = observer

    def bind(self, event_name, handler):
        self.events[event_name] = handler
        self.register_event(event_name)

    def unbind(self, event_name):
        del self.events[event_name]
        self.unregister_event(event_name)

    def handle_note(self, note):
        event_name = note["event_name"]
        self.events[event_name](note)

    def register_event(self, event_name):
        self.observer.register(event_name, self.handle_note, self.uid)

    def unregister_event(self, event_name):
        self.observer.unregister(event_name, self.uid)

    def unregister_all(self):
        for event_name in self.events:
            self.unregister_event(event_name)


class Controller(EventHandler):
    def __init__(self, observer):
        super(Controller, self).__init__(observer)

    def handle_note(self, note):
        event_name = note["event_name"]
        command = self.events[event_name]()
        command.handle_note(note)


class Facade(object):
    ''''''
    def __init__(self):
        ''''''
        self.model = ObjectStore()
        self.model_observer = Observer()
        self.view = ObjectStore()
        self.app_observer = Observer()
        self.controller = Controller(self.app_observer)
        self.gui_observer = Observer()

facade = Facade()


class ProxyMixin(object):
    ''''''
    def has_proxy(self, proxy_name):
        ''''''
        return facade.model.has_object(proxy_name)

    def register_proxy(self, proxy):
        ''''''
        return facade.model.register_object(proxy.name, proxy)

    def retrieve_proxy(self, proxy_name):
        return facade.model.retrieve_object(proxy_name)

    def remove_proxy(self, proxy_name):
        ''''''
        proxy = facade.model.remove_object(proxy_name)
        proxy.event_handler.unregister_all()


class MediatorMixin(object):

    def has_mediator(self, name):
        return facade.view.has_object(name)

    def register_mediator(self, mediator):
        return facade.view.register_object(mediator.name, mediator)

    def remove_medaitor(self, name):
        mediator = facade.view.remove_object(name)
        mediator.event_handler.unregister_all()
        mediator.gui_event_handler.unregister_all()


class NotifyAppMixin(object):

    def notify_app(self, event_name, data="", uid="", **kwargs):
        facade.app_observer.notify(event_name, data, uid, **kwargs)


class CommandMixin(object):

    def has_command(self, event_name):
        return event_name in facade.controller.events

    def register_command(self, event_name, command):
        facade.controller.bind(event_name, command)

    def remove_command(self, event_name):
        facade.controller.unbind(event_name)


class Ymvc(ProxyMixin, MediatorMixin, CommandMixin, NotifyAppMixin):
    pass


class Proxy(NotifyAppMixin, ProxyMixin):
    ''''''
    def __init__(self, name, data=""):
        self.event_handler = EventHandler(facade.model_observer)
        self.name = name
        self.data = data

    def on_register(self):
        '''Overwrite this method'''

    def on_remove(self):
        '''Overwrite this method'''

    def bind_proxy_event(self, event_name, handler):
        ''''''
        self.event_handler.bind(event_name, handler)

    def notify_proxys(self, event_name, data="", uid="", **kwargs):
        facade.model_observer.notify(event_name, data, uid, **kwargs)


class Mediator(Ymvc):
    def __init__(self, name, view):
        self.event_handler = EventHandler(facade.app_observer)
        self.gui_event_handler = EventHandler(facade.gui_observer)
        self.name = name
        self.view = view

    def on_register(self):
        '''Overwrite this method'''

    def on_remove(self):
        '''Overwrite this method'''

    def bind_gui(self, event_name, handler):
        self.gui_event_handler.bind((event_name, id(self.view)), handler)

    def bind_app_event(self, event_name, handler):
        self.event_handler.bind(event_name, handler)


class Command(Ymvc):
    def handle_note(self, note):
        '''Overwrite this'''
        raise NotImplementedError("Command handle_note")


class GuiEvent(object):
    def __init__(self, view):
        self.view_id = id(view)

    def notify(self, event_name, data="", uid="", **kwargs):
        facade.gui_observer.notify((event_name, self.view_id), data, uid,
                                   **kwargs)
