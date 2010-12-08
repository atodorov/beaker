XML-RPC methods
===============

These XML-RPC methods form part of the public API exposed by Beaker. The 
:command:`bkr` command-line client (distributed with Beaker) uses these methods 
to interact with the Beaker server. Users may also invoke them directly. The 
Python standard library includes an XML-RPC client library (:mod:`xmlrpclib`); 
the `Kobo`_ utility library may also be of interest.

The XML-RPC endpoint URL is ``/RPC2`` (relative to the base URL of the Beaker server).

Beaker uses XML-RPC internally for communication between the lab 
controller and the server. The internal API is not documented here.

.. _Kobo: https://fedorahosted.org/kobo/


Authentication
--------------

XML-RPC methods in the :mod:`auth` namespace allow the caller to begin or end an 
authenticated session with Beaker.

Beaker uses HTTP cookies to track sessions across XML-RPC calls. When calling 
the :meth:`auth.login_*` methods below, the response will include an HTTP 
cookie identifying the session. The caller must use this cookie in 
subsequent requests which belong with this session.

.. currentmodule:: bkr.server.authentication

.. automethod:: auth.login_krbV

.. automethod:: auth.login_password

.. automethod:: auth.logout()

.. automethod:: auth.who_am_i


Systems
-------

These XML-RPC methods allow the caller to manipulate systems in Beaker's 
inventory.

.. currentmodule:: bkr.server.systems

.. automethod:: systems.reserve

.. automethod:: systems.release

.. automethod:: systems.power

.. automethod:: systems.provision


Distros
-------

The following XML-RPC methods allow the caller to fetch and manipulate distros 
recorded in Beaker.

.. currentmodule:: bkr.server.distro

.. automethod:: distros.filter

.. automethod:: distros.edit_version

.. automethod:: distros.tag

.. automethod:: distros.untag


.. _task-library:

Task library
------------

These XML-RPC methods fetch and manipulate tasks in the Beaker task library.

.. currentmodule:: bkr.server.tasks

.. automethod:: tasks.to_dict

.. automethod:: tasks.filter

.. automethod:: tasks.upload


Running jobs
------------

.. currentmodule:: bkr.server.jobs

.. automethod:: jobs.upload

.. automethod:: jobs.list

.. automethod:: jobs.delete_jobs

.. currentmodule:: None

.. function:: recipes.tasks.extend(task_id, kill_time)

   Extends the watchdog for a running task.

   :param task_id: id of task to be extended
   :type task_id: integer
   :param kill_time: number of seconds by which to extend the watchdog
   :type kill_time: integer

.. function:: recipes.tasks.watchdog

   Returns number of seconds left on the watchdog for the given task, or False 
   if it doesn't exist.

   :param task_id: id of task
   :type task_id: integer

.. automodule:: bkr.server.task_actions

.. automethod:: taskactions.task_info(taskid)

.. automethod:: taskactions.to_xml

.. automethod:: taskactions.stop


General Beaker information
--------------------------

.. currentmodule:: None

.. function:: lab_controllers

   Returns an array containing the fully-qualified domain name of each lab 
   controller attached to the Beaker server.
