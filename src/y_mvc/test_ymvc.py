'''
Created on 29 Oct 2012

@author: Dave Wilson
'''

import unittest
import ymvc


class TestObserver(unittest.TestCase):

    def setUp(self):
        self.observer = ymvc.Observer()
        self.handle_note_value = None

    def tearDown(self):
        pass

    def test_register_single_event(self):
        self.observer.register("event1", "func", "uid")
        value = {'event1': {'uid': 'func'}}
        self.assertDictEqual(value, self.observer.observers)

    def test_register_two_events(self):
        self.observer.register("event1", "func", "uid")
        self.observer.register("event2", "func", "uid")
        value = {'event1': {'uid': 'func'},
                 'event2': {'uid': 'func'}}
        self.assertDictEqual(value, self.observer.observers)

    def test_register_same_event_name(self):
        self.observer.register("event1", "func", "uid")
        self.observer.register("event1", "func2", "uid")
        value = {'event1': {'uid': 'func'},
                 'event1': {'uid': 'func2'}}
        self.assertDictEqual(value, self.observer.observers)

    def test_notify(self):
        def callback(note):
            self.handle_note_value = note
        self.observer.register("event1", callback, "uid")
        self.observer.notify("event1", "data", "uid")
        value = {'event_name': 'event1', 'data': 'data', 'uid': 'uid'}
        self.assertEqual(value, self.handle_note_value)

    def test_notify_nobody(self):
        def callback(note):
            self.handle_note_value = note
        self.observer.register("event1", callback, "uid")
        self.observer.notify("event2", "data", "uid")
        value = None
        self.assertEqual(value, self.handle_note_value)

    def test_unregister(self):
        self.observer.register("event1", "func", "uid")
        self.observer.register("event2", "func", "uid")
        value = {'event1': {'uid': 'func'}}
        self.observer.unregister("event2", "uid")
        self.assertDictEqual(value, self.observer.observers)

    def test_unregister_removes_empty_dict(self):
        self.observer.register("event1", "func", "uid")
        self.observer.unregister("event1", "uid")
        self.assertDictEqual({}, self.observer.observers)


class TestUniqueDict(unittest.TestCase):

    def setUp(self):
        self.unique_dict = ymvc.UniqueDict()

    def test_raise_error_on_set_duplicate_item(self):
        self.unique_dict["key"] = "value"

        def duplicate():
            self.unique_dict["key"] = "value"
        self.assertRaises(KeyError, duplicate)

    def test_raise_get_non_existant(self):

        def get():
            return self.unique_dict["NonExistant"]
        self.assertRaises(KeyError, get)

    def test_raise_delete_non_existant(self):

        def delete():
            del self.unique_dict["NonExistant"]
        self.assertRaises(KeyError, delete)


class TestObjectStore(unittest.TestCase):

    def setUp(self):
        self.object_store = ymvc.ObjectStore()

    def create_object(self):
        class Obj(object):
            def __init__(self):
                self.on_register_called = False
                self.on_remove_called = False

            def on_register(self):
                self.on_register_called = True

            def on_remove(self):
                self.on_remove_called = True

        return Obj()

    def test_register_object(self):
        obj = self.create_object()
        self.object_store.register_object("obj_name", obj)
        self.assertIn("obj_name", self.object_store.unique_dict)

    def test_has_object(self):
        obj = self.create_object()
        self.object_store.register_object("obj_name", obj)
        self.assertTrue(self.object_store.has_object("obj_name"))

    def test_retrieve_object(self):
        obj = self.create_object()
        self.object_store.register_object("obj_name", obj)
        self.assertIs(obj, self.object_store.retrieve_object("obj_name"))

    def test_remove_object(self):
        obj = self.create_object()
        self.object_store.register_object("obj_name", obj)
        self.object_store.remove_object("obj_name")
        self.assertNotIn(obj, self.object_store.unique_dict)

    def test_on_register_called(self):
        obj = self.create_object()
        self.object_store.register_object("obj_name", obj)
        self.assertTrue(obj.on_register_called)

    def test_on_remove_called(self):
        obj = self.create_object()
        self.object_store.register_object("obj_name", obj)
        self.object_store.remove_object("obj_name")
        self.assertTrue(obj.on_remove_called)


class TestEventHandler(unittest.TestCase):

    def setUp(self):
        self.observer = ymvc.Observer()
        self.event_handler = ymvc.EventHandler(self.observer)

    def create_object(self):
        class Obj(object):
            def __init__(self):
                self.on_register_called = False
                self.on_remove_called = False
                self.note_value = None

            def handle_note(self, note):
                self.note_value = note

        return Obj()

    def test_bind(self):
        obj = self.create_object()
        self.event_handler.bind("event_name", obj)
        self.assertIn("event_name", self.event_handler.events)

    def test_unbind(self):
        obj = self.create_object()
        self.event_handler.bind("event_name", obj)
        self.event_handler.unbind("event_name")
        self.assertNotIn("event_name", self.event_handler.events)

    def test_handle_note(self):
        obj = self.create_object()
        self.event_handler.bind("event_name", obj.handle_note)
        self.observer.notify("event_name", "data", self.event_handler.uid)
        value = {'event_name': 'event_name',
                 'data': 'data',
                 'uid': self.event_handler.uid}
        self.assertEqual(value, obj.note_value)

    def test_register_event(self):
        self.event_handler.register_event("event_name")
        value = {'event_name':
                 {self.event_handler.uid: self.event_handler.handle_note}}
        self.assertEqual(value, self.observer.observers)

    def test_unregister_event(self):
        self.event_handler.register_event("event_name")
        self.event_handler.unregister_event("event_name")
        self.assertEqual({}, self.observer.observers)

    def test_unregister_all(self):
        obj = self.create_object()
        self.event_handler.bind("event_name", obj)
        self.event_handler.bind("event_name2", obj)
        self.event_handler.bind("event_name3", obj)
        self.assertEqual(3, len(self.observer.observers))
        self.event_handler.unregister_all()
        self.assertEqual({}, self.observer.observers)


class TestController(unittest.TestCase):

    def setUp(self):
        self.observer = ymvc.Observer()
        self.controller = ymvc.Controller(self.observer)

    def test_handle_note(self):

        class Obj(object):

            def handle_note(self, note):
                global note_value
                note_value = note

        self.controller.bind("event_name", Obj)
        self.observer.notify("event_name", "data")
        value = {'event_name': 'event_name',
                 'data': 'data',
                 'uid': ''}
        self.assertEqual(value, note_value)


class TestFacade(unittest.TestCase):

    def setUp(self):
        self.facade = ymvc.Facade()

    def test_model(self):
        self.assertIsInstance(self.facade.model, ymvc.ObjectStore)
        self.assertNotEqual(self.facade.model, self.facade.view)

    def test_model_observer(self):
        self.assertIsInstance(self.facade.model_observer, ymvc.Observer)
        self.assertNotEqual(self.facade.model_observer,
                            self.facade.app_observer)
        self.assertNotEqual(self.facade.model_observer,
                            self.facade.gui_observer)

    def test_view(self):
        self.assertIsInstance(self.facade.view, ymvc.ObjectStore)
        self.assertNotEqual(self.facade.model, self.facade.view)

    def test_app_observer(self):
        self.assertIsInstance(self.facade.app_observer, ymvc.Observer)
        self.assertNotEqual(self.facade.model_observer,
                            self.facade.app_observer)
        self.assertNotEqual(self.facade.model_observer,
                            self.facade.gui_observer)
        self.assertEqual(self.facade.app_observer,
                         self.facade.controller.observer)

    def test_controller(self):
        self.assertIsInstance(self.facade.controller, ymvc.Controller)
        self.assertEqual(self.facade.app_observer,
                         self.facade.controller.observer)

    def test_gui_observer(self):
        self.assertIsInstance(self.facade.gui_observer, ymvc.Observer)
        self.assertNotEqual(self.facade.model_observer,
                            self.facade.app_observer)
        self.assertNotEqual(self.facade.model_observer,
                            self.facade.gui_observer)


class TestProxyMixin(unittest.TestCase):

    def setUp(self):
        self.proxy_mixin = ymvc.ProxyMixin()
        self.facade = ymvc.Facade()
        ymvc.facade = self.facade

        class Obj(object):
            def __init__(self):
                self.event_handler = EventHandler()
                self.name = "TestObj"
                self.on_register_called = False
                self.on_remove_called = False

            def on_register(self):
                self.on_register_called = True

            def on_remove(self):
                self.on_remove_called = True

        class EventHandler(object):
            def __init__(self):
                self.on_unregister_all_called = False

            def unregister_all(self):
                self.on_unregister_all_called = True

        self.obj = Obj()

    def test_has_proxy(self):
        self.facade.model.register_object("TestObj", self.obj)
        self.assertTrue(self.proxy_mixin.has_proxy("TestObj"))

    def test_register_proxy(self):
        self.proxy_mixin.register_proxy(self.obj)
        self.assertTrue(self.facade.model.has_object("TestObj"))

    def test_retrive_proxy(self):
        self.facade.model.register_object("TestObj", self.obj)
        self.assertEqual(self.obj, self.proxy_mixin.retrieve_proxy("TestObj"))

    def test_remove_proxy(self):
        self.facade.model.register_object("TestObj", self.obj)
        self.proxy_mixin.remove_proxy("TestObj")
        self.assertFalse(self.facade.model.has_object("TestObj"))
        self.assertTrue(self.obj.event_handler.on_unregister_all_called)


class TestMediatorMixin(unittest.TestCase):

    def setUp(self):
        self.mediator_mixin = ymvc.MediatorMixin()
        self.facade = ymvc.Facade()
        ymvc.facade = self.facade

        class Obj(object):
            def __init__(self):
                self.event_handler = EventHandler()
                self.gui_event_handler = EventHandler()
                self.name = "TestObj"
                self.on_register_called = False
                self.on_remove_called = False

            def on_register(self):
                self.on_register_called = True

            def on_remove(self):
                self.on_remove_called = True

        class EventHandler(object):
            def __init__(self):
                self.on_unregister_all_called = False

            def unregister_all(self):
                self.on_unregister_all_called = True

        self.obj = Obj()

    def test_has_mediator(self):
        self.facade.view.register_object("TestObj", self.obj)
        self.assertTrue(self.mediator_mixin.has_mediator("TestObj"))

    def test_register_mediator(self):
        self.mediator_mixin.register_mediator(self.obj)
        self.assertTrue(self.facade.view.has_object("TestObj"))

    def test_remove_mediator(self):
        self.facade.view.register_object("TestObj", self.obj)
        self.mediator_mixin.remove_medaitor("TestObj")
        self.assertFalse(self.facade.view.has_object("TestObj"))
        self.assertTrue(self.obj.event_handler.on_unregister_all_called)
        self.assertTrue(self.obj.gui_event_handler.on_unregister_all_called)


class TestNotifyAppMixin(unittest.TestCase):

    def setUp(self):
        self.notify_app_mixin = ymvc.NotifyAppMixin()
        self.facade = ymvc.Facade()
        ymvc.facade = self.facade

        class Obj(object):
            def __init__(self):
                self.event_handler = EventHandler()
                self.gui_event_handler = EventHandler()
                self.name = "TestObj"
                self.on_register_called = False
                self.on_remove_called = False
                self.events = {"event_name": self.handle_note}

            def on_register(self):
                self.on_register_called = True

            def on_remove(self):
                self.on_remove_called = True

            def handle_note(self, note):
                global note_value
                note_value = note

        class EventHandler(object):
            def __init__(self):
                self.on_unregister_all_called = False

            def unregister_all(self):
                self.on_unregister_all_called = True

        self.obj = Obj()

    def test_notify_app(self):
        self.facade.view.register_object("TestObj", self.obj)
        self.facade.app_observer.register("test_notify_app",
                                          self.obj.handle_note, "uid")
        self.notify_app_mixin.notify_app("test_notify_app", "data", "uid")
        self.assertEqual("test_notify_app", note_value["event_name"])

if __name__ == "__main__":
    unittest.main()
