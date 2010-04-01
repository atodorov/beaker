#
# Copyright (C) 2008 bpeck@redhat.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from turbogears.database import session
from turbogears import controllers, expose, flash, widgets, validate, error_handler, validators, redirect, paginate, config, url
from turbogears import identity, redirect
from cherrypy import request, response
from kid import Element
from bkr.server.widgets import myPaginateDataGrid
from bkr.server.widgets import RecipeWidget
from bkr.server.widgets import RecipeTasksWidget
from bkr.server.widgets import SearchBar
from bkr.server import search_utility
from bkr.server.xmlrpccontroller import RPCRoot
from bkr.server.helpers import *
from bkr.server.recipetasks import RecipeTasks
from socket import gethostname
from upload import Uploader
import exceptions
import time

import cherrypy

from model import *
import string

import logging
log = logging.getLogger(__name__)

class Recipes(RPCRoot):
    # For XMLRPC methods in this class.
    exposed = True

    hidden_id = widgets.HiddenField(name='id')
    confirm = widgets.Label(name='confirm', default="Are you sure you want to cancel?")
    message = widgets.TextArea(name='msg', label=_(u'Reason?'), help=_(u'Optional'))

    cancel_form = widgets.TableForm(
        'cancel_recipe',
        fields = [hidden_id, message, confirm],
        action = 'really_cancel',
        submit_text = _(u'Yes')
    )

    tasks = RecipeTasks()

    recipe_widget = RecipeWidget()
    recipe_tasks_widget = RecipeTasksWidget()

    upload = Uploader(config.get("basepath.logs", "/var/www/beaker/logs"))

    @cherrypy.expose
    @identity.require(identity.not_anonymous())
    def upload_file(self, recipe_id, path, name, size, md5sum, offset, data):
        """
        upload to recipe in pieces 
        """
        try:
            recipe = Recipe.by_id(recipe_id)
        except InvalidRequestError:
            raise BX(_('Invalid recipe ID: %s' % recipe_id))

       # Add the log to the DB if it hasn't been recorded yet.
        if LogRecipe(path,name) not in recipe.logs:
            recipe.logs.append(LogRecipe(path, name))

        return self.upload.uploadFile("%s/%s" % (recipe.filepath, path), 
                                      name, 
                                      size, 
                                      md5sum, 
                                      offset, 
                                      data)

    @cherrypy.expose
    @identity.require(identity.not_anonymous())
    def stop(self, recipe_id, stop_type, msg=None):
        """
        Set recipe status to Completed
        """
        try:
            recipe = Recipe.by_id(recipe_id)
        except InvalidRequestError:
            raise BX(_('Invalid recipe ID: %s' % recipe_id))
        if stop_type not in recipe.stop_types:
            raise BX(_('Invalid stop_type: %s, must be one of %s' %
                             (stop_type, recipe.stop_types)))
        kwargs = dict(msg = msg)
        return getattr(recipe,stop_type)(**kwargs)

    @cherrypy.expose
    def system_xml(self, system_name=None):
        """ 
            Pass in system name and you'll get the active recipe
               for that system.
        """
        if not system_name:
            raise BX(_("Missing system name!"))
        try:
            system = System.by_fqdn(system_name,identity.current.user)
        except InvalidRequestError:
            raise BX(_("Invalid system %s" % system_name))
        try:
            recipexml = Watchdog.by_system(system).recipe.to_xml().toprettyxml()
        except InvalidRequestError:
            raise BX(_("No active recipe for %s" % system_name))
        return recipexml

    @cherrypy.expose
    def to_xml(self, recipe_id=None):
        """ 
            Pass in recipe id and you'll get that recipe's xml
        """
        if not recipe_id:
            raise BX(_("No recipe id provided!"))
        try:
           recipexml = Recipe.by_id(recipe_id).to_xml().toprettyxml()
        except InvalidRequestError:
            raise BX(_("Invalid Recipe ID %s" % recipe_id))
        return recipexml

    def _recipe_search(self,recipe,**kw):
        recipe_search = search_utility.Recipe.search(recipe)
        for search in kw['recipesearch']:
            col = search['table'] 
            recipe_search.append_results(search['value'],col,search['operation'],**kw)
        return recipe_search.return_results()

    def _recipes(self,recipe,**kw):
        return_dict = {}                    
        if 'simplesearch' in kw:
            simplesearch = kw['simplesearch']
            kw['recipesearch'] = [{'table' : 'Id',   
                                   'operation' : 'is', 
                                   'value' : kw['simplesearch']}]                    
        else:
            simplesearch = None

        return_dict.update({'simplesearch':simplesearch})

        if kw.get("recipesearch"):
            searchvalue = kw['recipesearch']
            recipes_found = self._recipe_search(recipe,**kw)
            return_dict.update({'recipes_found':recipes_found})
            return_dict.update({'searchvalue':searchvalue})
        return return_dict

    @expose(template='bkr.server.templates.grid')
    @paginate('list',default_order='-id', limit=50)
    def index(self,*args,**kw):
        return self.recipes(recipes=session.query(MachineRecipe),*args,**kw)

    @identity.require(identity.not_anonymous())
    @expose(template='bkr.server.templates.grid')
    @paginate('list',default_order='-id', limit=50)
    def mine(self,*args,**kw):
        return self.recipes(recipes=MachineRecipe.mine(identity.current.user),*args,**kw)

    def recipes(self,recipes,action='.',*args, **kw): 
        recipes_return = self._recipes(recipes,**kw)
        searchvalue = None
        search_options = {}
        if recipes_return:
            if 'recipes_found' in recipes_return:
                recipes = recipes_return['recipes_found']
            if 'searchvalue' in recipes_return:
                searchvalue = recipes_return['searchvalue']
            if 'simplesearch' in recipes_return:
                search_options['simplesearch'] = recipes_return['simplesearch']

        recipes_grid = myPaginateDataGrid(fields=[
		     widgets.PaginateDataGrid.Column(name='id', getter=lambda x:make_link(url='./%s' % x.id, text=x.t_id), title='ID', options=dict(sortable=True)),
		     widgets.PaginateDataGrid.Column(name='whiteboard', getter=lambda x:x.whiteboard, title='Whiteboard', options=dict(sortable=True)),
		     widgets.PaginateDataGrid.Column(name='arch', getter=lambda x:x.arch, title='Arch', options=dict(sortable=True)),
		     widgets.PaginateDataGrid.Column(name='system', getter=lambda x: x.system and x.system.link, title='System', options=dict(sortable=True)),
		     widgets.PaginateDataGrid.Column(name='distro', getter=lambda x: x.distro and x.distro.link, title='Distro', options=dict(sortable=True)),
		     widgets.PaginateDataGrid.Column(name='progress', getter=lambda x: x.progress_bar, title='Progress', options=dict(sortable=False)),
		     widgets.PaginateDataGrid.Column(name='status.status', getter=lambda x:x.status, title='Status', options=dict(sortable=True)),
		     widgets.PaginateDataGrid.Column(name='result.result', getter=lambda x:x.result, title='Result', options=dict(sortable=True)),
                     widgets.PaginateDataGrid.Column(name='action', getter=lambda x:x.action_link, title='Action', options=dict(sortable=False)),
                    ])

        search_bar = SearchBar(name='recipesearch',
                           label=_(u'Recipe Search'),    
                           table = search_utility.Recipe.search.create_search_table(),
                           search_controller=url("/get_search_options_recipe"), 
                           )
        return dict(title="Recipes", grid=recipes_grid, list=recipes, search_bar=search_bar,action=action,options=search_options,searchvalue=searchvalue)

    @identity.require(identity.not_anonymous())
    @expose()
    def really_cancel(self, id, msg=None):
        """
        Confirm cancel recipe
        """
        try:
            recipe = Recipe.by_id(id)
        except InvalidRequestError:
            flash(_(u"Invalid recipe id %s" % id))
            redirect(".")
        if not identity.current.user.is_admin() and recipe.recipeset.job.owner != identity.current.user:
            flash(_(u"You don't have permission to cancel recipe id %s" % id))
            redirect(".")
        recipe.cancel(msg)
        flash(_(u"Successfully cancelled recipe %s" % id))
        redirect(".")

    @identity.require(identity.not_anonymous())
    @expose(template="bkr.server.templates.form")
    def cancel(self, id):
        """
        Confirm cancel recipe
        """
        try:
            recipe = Recipe.by_id(id)
        except InvalidRequestError:
            flash(_(u"Invalid recipe id %s" % id))
            redirect(".")
        if not identity.current.user.is_admin() and recipe.recipeset.job.owner != identity.current.user:
            flash(_(u"You don't have permission to cancel recipe id %s" % id))
            redirect(".")
        return dict(
            title = 'Cancel Recipe %s' % id,
            form = self.cancel_form,
            action = './really_cancel',
            options = {},
            value = dict(id = recipe.id,
                         confirm = 'really cancel recipe %s?' % id),
        )

    @expose(template="bkr.server.templates.recipe")
    def default(self, id):
        try:
            recipe = Recipe.by_id(id)
        except InvalidRequestError:
            flash(_(u"Invalid recipe id %s" % id))
            redirect(".")
        return dict(title   = 'Recipe',
                    recipe_widget        = self.recipe_widget,
                    recipe_tasks_widget  = self.recipe_tasks_widget,
                    recipe               = recipe)
