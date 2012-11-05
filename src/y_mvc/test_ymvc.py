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
                print "called"
                global note_value
                note_value = note
        self.controller.bind("event_name", Obj)
        self.observer.notify("event_name", "data")
        value = {'event_name': 'event_name',
                 'data': 'data',
                 'uid': ''}
        self.assertEqual(value, note_value)

if __name__ == "__main__":
    unittest.main()
