#! /usr/bin/python

import unittest
import scooter
from scooter_types import *
from parser import *
import testdata

q = scooter.q

def pipeline(ops):
    before = 0
    result = []
    for i, op in enumerate(ops):
        result.append(edit(before, op, str(i + 1)))
        before = str(i + 1)
    return result
        
class ScooterTest(unittest.TestCase):        
    def test_edits(self):
        t = self.assertQueryPipelineContentsEqual
        t([noop()], ""),
        t([append("foo")], "foo")
        t([append("foo"), noop()], "foo")
        t([append("foo"), append("bar")], "foobar")
        t([append("foo"), append("baz")], "foobaz")
        t([append("foo"), trim(1)], "oo")
        t([append("foo"), trim(3)], "")
        t([append("foo"), trim(1000)], "")
        t([append("foo"), limit(2)], "fo")
        t([append("foo"), limit(0)], "")
        t([append("foo"), limit(1000)], "foo")
        t([append("bar"), trim(1), limit(1)], "a")
        t([append("bar"), trim(1000), limit(1000)], "")
        t([append("foobar"), insert(0, "hello")], "hellofoobar")
        t([append("foobar"), insert(1, "hello")], "fhellooobar")
        t([append("foobar"), insert(10, "hello")], "foobar    hello")
        t([append("foobar"), put(0, "hello")], "hellor")
        t([append("foobar"), put(1, "hello")], "fhello")
        t([append("foobar"), put(2, "hello")], "fohello")
        t([append("foobar"), put(10, "hello")], "foobar    hello")
        t([append("foo"), proc("md5")], "acbd18db4cc2f85cedef654fccc4a4d8\n")
        t([append("foo"),proc("md5")], "acbd18db4cc2f85cedef654fccc4a4d8\n")
        t([append("foo"),proc("md5")], "acbd18db4cc2f85cedef654fccc4a4d8\n")
        t([append("foo\n"),proc("md5")], "d3b07384d113edec49eaa6238ad5ff00\n")
        t([append("foo"),proc("openssl sha1")], "0beec7b5ea3f0fdbc95d0dd47f3c5bc275da8a33\n")
        t([append("foo"), func("md5")], "acbd18db4cc2f85cedef654fccc4a4d8\n")

    def test_state_reuse(self):
        self.assertEqual(
            q([]).id,
            q([]).id)

        self.assertNotEqual(
            q([]).id,
            q(pipeline([append("foo")])).id)
        
        self.assertEqual(
            q(pipeline([append("foo")])).id,
            q(pipeline([append("foo")])).id)
        
        self.assertEqual(
            q(pipeline([append("foo"), append("bar")])).id,
            q(pipeline([append("foo"), append("bar")])).id)
        
        self.assertNotEqual(
            q(pipeline([append("foo"), append("bar")])).id,
            q(pipeline([append("foo"), append("baz")])).id)

        first = q(pipeline(
            [append("foo"),
             proc("python -c'import time; print repr(time.time())'")]))
        second = q(pipeline(
            [append("foo"),
             proc("python -c'import time; print repr(time.time())'")]))
        
        self.assertNotEqual(first.id, second.id)
        self.assertNotEqual(first.contents, second.contents)

        first = q(pipeline(
            [append("foo"),
             func("python -c'import time; print repr(time.time())'")]))
        second = q(pipeline(
            [append("foo"),
             func("python -c'import time; print repr(time.time())'")]))
        self.assertEqual(first.id, second.id)
        self.assertEqual(first.contents, second.contents)

        # TODO(dbentley): we would like if an invocation of func
        # reused a proc. But that does not work yet and is not worth
        # the complication.
        # first = q(pipeline(
        #     [append("bar"),
        #      proc("python -c'import time; print repr(time.time())'")]))
        # second = q(pipeline(
        #     [append("bar"),
        #      func("python -c'import time; print repr(time.time())'")]))
        # self.assertEqual(first.contents, second.contents)
        # self.assertEqual(first.id, second.id)

    def testCat(self):
        foo = q([edit(0, append("foo"))])
        bar = q([edit(0, append("bar"))])
        baz = q([edit(0, append("baz"))])
        foobar = q([scooter.Statement(
            [foo.id, bar.id], cat(), ["_"])])
        self.assertEqual("foobar", foobar.contents)
        foobarbaz = q([scooter.Statement(
            [foo.id, bar.id, baz.id], cat(), ["_"])])
        self.assertEqual("foobarbaz", foobarbaz.contents)
        
    def test_dirs(self):
        self.assertEqual(
            "hello world",
            q([
                edit(0, append("hello world"), "hello"),
                Stmt([0, "hello"], setfile("foo"), ["dir"]),
                Stmt(["dir"], getfile("foo"), ["_"])
                ]).contents)

    def test_propagation(self):
        dir = q([
            edit(0, append("hello world"), "hello"),
            edit(0, append("go gentle"), "gentle"),
            Stmt([0, "hello", "gentle"], setfile("hello", "gentle"), ["_"])])
        hello_digest = q([
            Stmt([dir.id], getfile("hello"), ["hello"]),
            Stmt(["hello"], func("md5; python -c'import time; print repr(time.time())'"), ["_"])
            ])
        modified_dir = q([
            edit(0, append("do not go gentle"), "do_not"),
            Stmt([dir.id, "do_not"], setfile("gentle"), ["_"])])
        modified_hello_digest = q([
            Stmt([modified_dir.id], getfile("hello"), ["hello"]),
            Stmt(["hello"], func("md5; python -c'import time; print repr(time.time())'"), ["_"])
            ])
        self.assertEqual(hello_digest.contents, modified_hello_digest.contents)

    def test_recursive_q(self):
        foo_text = q([edit(0, append("foo"))]).id
        bar_text = q([edit(0, append("bar"))]).id
        proc_stamp_q = q([edit(0, append("""[
            Stmt("0", proc("md5; python -c'import time; print repr(time.time())'"), ["_"])
        ]"""))]).id
        proc_unstamp_q = q([edit(0, append("""[
            Stmt("0", proc("md5"), ["_"])
        ]"""))]).id
        func_stamp_q = q([edit(0, append("""[
            Stmt("0", func("md5; python -c'import time; print repr(time.time())'"), ["_"])
        ]"""))]).id
        func_unstamp_q = q([edit(0, append("""[
            Stmt("0", func("md5"), ["_"])
        ]"""))]).id
        a = q([Stmt([proc_unstamp_q, foo_text], recur(), ["_"])])
        b = q([Stmt([proc_unstamp_q, foo_text], recur(), ["_"])])
        self.assertEquals(a.contents, b.contents)
        a = q([Stmt([proc_stamp_q, foo_text], recur(), ["_"])])
        b = q([Stmt([proc_stamp_q, foo_text], recur(), ["_"])])
        self.assertNotEqual(a.contents, b.contents)
        
        a = q([Stmt([func_unstamp_q, foo_text], recur(), ["_"])])
        b = q([Stmt([func_unstamp_q, foo_text], recur(), ["_"])])
        self.assertEquals(a.contents, b.contents)
        a = q([Stmt([func_stamp_q, foo_text], recur(), ["_"])])
        b = q([Stmt([func_stamp_q, foo_text], recur(), ["_"])])
        self.assertEquals(a.contents, b.contents)        

    def test_compile(self):
        hello_world_text = q([edit(0, append(
            '#include <stdio.h>\nint main(int argc, char** argv){\n'
            '  printf("Hello World.\\n");\n  return 0;\n}'))]).id
        a_out_text = q([
            Stmt([0, hello_world_text],
                 func('gcc hello.c && cat a.out', 'hello.c'), ['_'])]).id
        results = q([
            Stmt([0, a_out_text], func('chmod +x a.out && ./a.out', 'a.out'), ['_'])]).contents
        self.assertEquals('Hello World.\n', results)

    def test_dunts(self):
        dunts_text = q([edit(0, append(testdata.file_text('dunts.py')))]).id
        build_text = q([edit(0, append(testdata.file_text('BUILD')))]).id
        pass_text = q([edit(0, append(
            '#include <stdio.h>\nint main(int argc, char** argv){\n'
            '  printf("PASS:tweetstest.\\n");\n  return 0;\n}'))]).id
        snapshot = q([Stmt([0, dunts_text, build_text, pass_text],
                           setfile("dunts.py", "BUILD", "tweetstest.c"), ["_"])]).id
        plan = q(
            [Stmt([0, dunts_text, build_text], func("chmod +x dunts.py && ./dunts.py", "$@D", "dunts.py", "BUILD"), ["plans"]),
             Stmt(["plans"], getfile("all"), ["_"]),
        ]).id
        result = q([Stmt([plan, snapshot], recur(), ["_"])]).contents
        self.assertEqual("PASS:tweetstest.\n", result)
        
    def assertQueryPipelineContentsEqual(self, ops, expected):
        self.assertEqual(expected, q(pipeline(ops)).contents)


if __name__ == '__main__':
    unittest.main()
