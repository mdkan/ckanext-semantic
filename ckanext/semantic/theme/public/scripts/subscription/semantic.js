var cache = {};
$.ajax(
{
    url: "/vocabulary",
    dataType: "json",
    success: function( data )
    {
        for(index = 0; index < data.length; index += 1)
        {
            data[index].value = data[index].title + data[index].prefix
            data[index].id = data[index].vocabulary
        }
        
        $('topic_input').autocomplete(
        {
            source: data,
            minLength: 0,
            focus: function( event, ui ) {
                $("#topic_input").val(ui.item.vocabulary);
                
                return false;
            },
            select: function( event, ui )
            {
                $('#topic_input').val(ui.item.vocabulary)
                
                return false;
            }
        }).data("autocomplete")._renderItem = function( ul, item )
        {
            return $( "<li>" )
                .data( "item.autocomplete", item )
                .append( '<a><b>' + item.title + '</b><br /><b>Prefix:</b> ' + item.prefix + '<br /><b>URI:</b> ' + item.vocabulary + '</a>' )
                .appendTo( ul );
        }
    }
});
