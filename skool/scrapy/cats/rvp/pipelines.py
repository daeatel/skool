# -*- coding: utf-8 -*-
from treelib import Tree
from skool.utils import makepath


class TreePipeline(object):

    def open_spider(self, spider):
        self.tree = Tree()
        self.tree.create_node("root", "root")

    def process_item(self, item, spider):
        lst = item['text']
        lst = [x.strip() for x in [y.replace('...', '') for y in lst]]
        item['pagetitle'] = item['pagetitle'].replace('...', '')
        lst[-1] = item['pagetitle']
        for idx, elem in enumerate(lst):
            if idx == 0:
                previous = "root"
            else:
                previous = "|".join(lst[:idx])
            elem = "|".join(lst[:idx + 1])
            # elem = elem.replace('...', '')
            elem = elem.encode('utf-8').decode('utf-8')
            if not self.tree.contains(elem):
                print "Adding node %s" % elem
                self.tree.create_node(elem, elem, parent=previous)
                # self.tree.show()
        return item

    def close_spider(self, spider):
        self.tree.show()
        with open(makepath('data/cats/tree.json'), 'w') as outfile:
            outfile.write(self.tree.to_json())
        self.tree.save2file(makepath('data/cats/tree.tree'))
