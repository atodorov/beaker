# -*- coding: utf-8 -*-


from bkr.client.task_watcher import *
from bkr.client import BeakerCommand, BeakerWorkflow, BeakerJob, BeakerRecipeSet, BeakerRecipe
from optparse import OptionValueError
import sys
import xml.dom.minidom

class Workflow_Simple(BeakerWorkflow):
    """Simple workflow to generate job to scheduler"""
    enabled = True
    doc = xml.dom.minidom.Document()

    def options(self):
        super(Workflow_Simple, self).options()
        self.parser.usage = "%%prog %s [options]" % self.normalized_name

    def run(self, *args, **kwargs):
        username = kwargs.get("username", None)
        password = kwargs.get("password", None)

        # get all tasks requested
        requestedTasks = self.getTasks(*args, **kwargs)

        debug  = kwargs.get("debug", False)
        dryrun = kwargs.get("dryrun", False)
        nowait = kwargs.get("nowait", False)
	family = kwargs.get("family", None)
	distro = kwargs.get("distro", None)
	arches = kwargs.get("arch", [])
	taskParams = kwargs.get("taskparam", [])

        if not family and not distro:
            sys.stderr.write("No Family or Distro specified\n")
            sys.exit(1)

        if not arches:
            sys.stderr.write("No arches specified, you must specify at least one\n")
            sys.exit(1)

        if not requestedTasks:
            sys.stderr.write("You must specify a package, type or task to run\n")
            sys.exit(1)

        # Create Job
        job = BeakerJob(*args, **kwargs)

        # Create Base Recipe
        recipeTemplate = BeakerRecipe()

        # Add Distro Requirements
        recipeTemplate.addBaseRequires(*args, **kwargs)

        # Add Host Requirements


        for arch in arches:
            arch_node = self.doc.createElement('distro_arch')
            arch_node.setAttribute('op', '=')
            arch_node.setAttribute('value', arch)
            if self.multi_host:
                recipeSet = BeakerRecipeSet()
                for i in range(self.n_servers):
                    recipeSet.addRecipe(self.processTemplate(recipeTemplate, 
                                                             requestedTasks,
                                                             taskParams=taskParams,
                                                             distroRequires=arch_node, 
                                                             role='SERVERS'))
                for i in range(self.n_clients):
                    recipeSet.addRecipe(self.processTemplate(recipeTemplate, 
                                                             requestedTasks,
                                                             taskParams=taskParams,
                                                             distroRequires=arch_node, 
                                                             role='CLIENTS'))
                job.addRecipeSet(recipeSet)
            else:
                job.addRecipe(self.processTemplate(recipeTemplate,
                                                   requestedTasks,
                                                   taskParams=taskParams,
                                                   distroRequires=arch_node))

        # jobxml
        jobxml = job.toxml(**kwargs)

        if debug:
            print jobxml

        self.set_hub(username, password)
        submitted_jobs = []
        failed = False

        if not dryrun:
            try:
                submitted_jobs.append(self.hub.jobs.upload(jobxml))
            except Exception, ex:
                failed = True
                print ex
        if not dryrun:
            if not nowait:
                TaskWatcher.watch_tasks(self.hub, submitted_jobs)
            if failed:
                sys.exit(1)