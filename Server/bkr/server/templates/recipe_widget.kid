<div xmlns:py="http://purl.org/kid/ns#">

<script type="text/javascript">
function showall_${recipe.id}()
{
    $('.recipe_${recipe.id}').show();
    $('.hide_recipe_${recipe.id}').show();
    $('.fail_show_recipe_${recipe.id}').show();
    $('.all_show_recipe_${recipe.id}').hide();
    $.cookie('recipe_${recipe.id}','all')
}

function showfail_${recipe.id}()
{
    $('.recipe_${recipe.id}').hide();
    $('.fail_recipe_${recipe.id}').show();
    $('.hide_recipe_${recipe.id}').show();
    $('.all_show_recipe_${recipe.id}').show();
    $('.fail_show_recipe_${recipe.id}').hide();
    $.cookie('recipe_${recipe.id}','fail')
}

function shownone_${recipe.id}()
{
    $('.recipe_${recipe.id}').hide();
    $('.all_show_recipe_${recipe.id}').show();
    $('.fail_show_recipe_${recipe.id}').show();
    $('.hide_recipe_${recipe.id}').hide();
    $.cookie('recipe_${recipe.id}',null)
}

$(document).ready(function() {
    if($.cookie('recipe_${recipe.id}')) 
    {
       switch ($.cookie('recipe_${recipe.id}'))
       {
        case 'all':
            showall_${recipe.id}();
        break;
        case 'fail':
            showfail_${recipe.id}();
        break;
       }
    } else {
        shownone_${recipe.id}();
    }

    $('#all_recipe_${recipe.id}').click( function() { showall_${recipe.id}(); });
    $('#failed_recipe_${recipe.id}').click( function() { showfail_${recipe.id}(); });
    $('#hide_recipe_${recipe.id}').click( function() { shownone_${recipe.id}(); });
    $('#logs_button_${recipe.id}').click(function () { $('#logs_${recipe.id}').toggleClass('hidden', 'addOrRemove'); });

});
</script>

 <table class="show">
  <tr>
   <td class="title"><b>Recipe ID</b></td>
   <td class="value"><a class="list" href="${tg.url('/recipes/%s' % recipe.id)}">${recipe.t_id}</a></td>
   <td class="title"><b>Progress</b></td>
   <td class="value">${recipe.progress_bar}</td>
   <td class="title"><b>Status</b></td>
   <td class="value">${recipe.status}</td>
   <td class="title"><b>Result</b></td>
   <td class="value">${recipe.result}</td>
  </tr>
  <tr>
   <td class="title"><b>Distro</b></td>
   <td class="value">${recipe.distro.link}</td>
   <td class="title"><b>Arch</b></td>
   <td class="value">${recipe.arch}</td>
   <td class="title"><b>Family</b></td>
   <td class="value">${recipe.distro.osversion}</td>
   <td class="title"><b>Action(s)</b></td>
   <td class="value">${recipe.action_link}</td>
  </tr>
  <tr>
   <td class="title"><b>Queued</b></td>
   <td class="value">${recipe.recipeset.queue_time}</td>
   <td class="title"><b>Started</b></td>
   <td class="value">${recipe.start_time}</td>
   <td class="title"><b>Finsihed</b></td>
   <td class="value">${recipe.finish_time}</td>
   <td class="title"><b>Duration</b></td>
   <td class="value">${recipe.duration}</td>
  </tr>
  <tr py:if="recipe.system">
   <td class="title"><b>System</b></td>
   <td class="value" colspan="8">${recipe.system.link}</td>
  </tr>
  <tr>
   <td class="title"><b>Whiteboard</b></td>
   <td class="value" colspan="8">${recipe.whiteboard}</td>
  </tr>
  <tr>
   <td class="title"><button id="logs_button_${recipe.id}">Logs</button></td>
   <td id="logs_${recipe.id}" class="hidden value" colspan="8"><br py:for="log in recipe.logs">${log.link}</br></td>
  </tr>
  <tr py:if="recipe.systems">
   <td class="title"><b>Possible Systems</b></td>
   <td class="value" colspan="8">${len(recipe.systems)}</td>
  </tr>
  <tr>
   <td colspan="9">
    <button class="all_show_recipe_${recipe.id}" id="all_recipe_${recipe.id}">
      Show All Results
    </button>
    <button py:if="recipe.is_failed()" class="fail_show_recipe_${recipe.id}" id="failed_recipe_${recipe.id}">
      Show Failed Results
    </button>
    <button class="hide_recipe_${recipe.id}" id="hide_recipe_${recipe.id}">
     Hide Results
    </button>
   </td>
  </tr>
 </table>

 <div py:if="recipe_tasks_widget" class="hidden recipe-tasks fail_recipe_${recipe.id} recipe_${recipe.id}">
  <h2>Task Runs</h2>
  <p py:content="recipe_tasks_widget(tasks=recipe.all_tasks)">Recipe Tasks goes here</p>
 </div>
</div>
