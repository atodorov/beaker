<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">

 <head>
  <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
  <title>${title} ${value.id}:${value.name}</title>
 </head>


 <body class="flora">
  <h2>Distro</h2>
  <table class="list">
   <tr class="list">
    <th class="list">
      <b>ID</b>
    </th>
    <td class="list" colspan="3">
     ${value.id}
    </td>
   </tr>
   <tr class="list">
    <th class="list">
      <b>Name</b>
    </th>
    <td class="list" colspan="3">
     ${value.name}
    </td>
   </tr>
   <tr class="list">
    <th class="list">
      <b>Date Created</b>
    </th>
    <td class="list" colspan="3">
     <span class="datetime">${value.date_created}</span>
    </td>
   </tr>
   <tr class="list">
    <th class="list">
      <b>OS Version</b>
    </th>
    <td class="list" colspan="3">
     ${value.osversion}
    </td>
   </tr>
  </table>
  <div><h2>Distro Trees</h2>
    <table class="list">
      <thead>
        <tr class="list">
          <th class="list">ID</th>
          <th class="list">Variant</th>
          <th class="list">Arch</th>
          <th class="list">Provision</th>
        </tr>
      </thead>
      <tbody>
        <tr py:for="i, tree in enumerate(value.trees)" class="${i%2 and 'odd' or 'even'}">
          <td class="list"><a class="list" href="${tg.url('/distrotrees/%s' % tree.id)}">${tree.id}</a></td>
          <td class="list">${tree.variant}</td>
          <td class="list">${tree.arch}</td>
          <td class="list">
            <span py:if="tree.lab_controller_assocs" py:strip="True">
              <a class="list" href="${tg.url('/reserve_system', distro_tree_id=tree.id)}">Pick System</a>
              <span style="padding-left: 1em;" />
              <a class="list" href="${tg.url('/reserveworkflow/reserve', distro_tree_id=tree.id)}">Pick Any System</a>
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <div><h2>Tags</h2>
   ${form.display(method='get', action=action, value=value, options=options)}
  </div>
  <div><h2>Executed Tasks</h2>
    ${form_task.display(
    value=value_task,
    options=options,
    action=action_task,
    target_dom='task_items',
    update='task_items',
    )}
    <div id="task_items">&nbsp;</div>
  </div>
 </body>
</html>
