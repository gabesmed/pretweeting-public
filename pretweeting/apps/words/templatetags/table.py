from django.template import NodeList,Template,Context,Variable,Library,Node,Variable,loader
from django.template import TemplateSyntaxError,VariableDoesNotExist
import math
register=Library()

class TableNode(Node):
	def __init__(self, cellvar, sequence, cols, cellnodes):
		self.cellvar=cellvar
		self.sequence=sequence
		self.cols=cols
		self.cellnodes=cellnodes
	
	def __iter__(self):
		for node in self.cellnodes: yield node
	
	def get_nodes_by_type(self,nodetype):
		nodes=[]
		if isinstance(self,nodetype): nodes.append(self)
		nodes.extend(self.cellnodes.get_nodes_by_type(nodetype))
		return nodes
	
	def render(self,context):
		nodelist=NodeList()
		if context.has_key('parenttable'): parenttable=context['parenttable']
		else: parenttable={}
		context.push()
		try: values=self.sequence.resolve(context,True)
		except VariableDoesNotExist: values=[]
		if not values: values=[]
		if not hasattr(values,'__len__'):values=list(values)
		len_values=len(values)
		innernodelist=NodeList()
		totalrows=int(math.ceil(float(len_values)/float(self.cols)))
		rowcount=0
		for i, item in enumerate(values):
			loopctx={
				'counter0':i,
				'counter':i+1,
				'rowcounter0':(i/self.cols),
				'rowcounter':((i/self.cols)+1),
				'firstrow':(i<self.cols),
				'lastrow':(i>len_values-self.cols),
				'firstcell':(i==0),
				'lastcell':(i==len_values-1),
				'evencol':(i%2)==0,
				'oddcol':(i%2)==1,
				'parenttable':parenttable,
			}
			context[self.cellvar]=item
			loopctx['oddrow']=False
			loopctx['evenrow']=False
			loopctx['lastcellinrow']=False
			loopctx["startrow"]=False
			loopctx["endrow"]=False
			if totalrows==1 and i==len_values-1: loopctx['lastcellinrow']=True
			elif i==(len_values-1): loopctx['lastcellinrow']=True
			if i % self.cols==0:
				nodelist.append(innernodelist.render(context))
				innernodelist=NodeList()
				loopctx["startrow"]=True
				if (rowcount+1)%2==0:
					loopctx["oddrow"]=False
					loopctx["evenrow"]=True
				else:
					loopctx["oddrow"]=True
					loopctx["evenrow"]=False
			elif (i+1) % self.cols==0:
				loopctx['lastcellinrow']=True
				loopctx["endrow"]=True
				rowcount+=1
			context['table']=loopctx
			for node in self.cellnodes: innernodelist.append(node.render(context))
		if innernodelist and len(innernodelist)>0: nodelist.append(innernodelist.render(context))
		context.pop()
		return nodelist.render(context)

@register.tag(name="table")
def do_table(parser,token):
	"""
	Tag to help rendering tables. Replicates the django for tag,
	but add's in more helpers specific to tables.
	
	{{table.counter0}}
	{{table.counter}}
	{{table.rowcounter0}}
	{{table.rowcounter}}
	{{table.startrow}}
	{{table.endrow}}
	{{table.oddrow}}
	{{table.evenrow}}
	{{table.firstrow}}
	{{table.lastrow}}
	{{table.firstcell}}
	{{table.lastcell}}
	{{table.lastcellinrow}}
	{{table.evencol}}
	{{table.oddcol}}
	{{table.parenttable}}
	
	EX:
	(this is a some what more complicated example, which
	hopefully illustrates this tags use better):
	<table width="100%">
		{% table genre artist.genres.all 5 %}
			{% if table.startrow %}
				{% if table.oddrow %}
				<tr class="highlight">
				{% else %}
				<tr>
				{% endif %}
			{% endif %}
			{% if table.lastcellinrow %}
				<td class="{% if table.oddrow %}highlightableCell {% endif %}cellAutoAdjust removeableGenre">
			{% else %}
				<td class="{% if table.oddrow %}highlightableCell {% endif %}left cellAutoAdjust removeableGenre">
			{% endif %}
				<div class="options displayNone"></div>
				{{genre.name}}
				</td>
			{% if table.endrow %}
			</tr>
			{% endif %}
		{% endtable %}
	</table>
	"""
	bits=token.contents.split()
	cellvar=bits[1]
	sequence=parser.compile_filter(bits[2])
	cols=int(bits[3])
	cellnodes=parser.parse(('endtable',))
	parser.delete_first_token()
	return TableNode(cellvar,sequence,cols,cellnodes)
