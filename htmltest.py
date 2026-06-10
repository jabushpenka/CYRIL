html = """
<!DOCTYPE html>
<html>
    <head>
        <title>CYRIL</title>
    </head>
    <body>
        <h1>Приходящие сообщения</h1>
        <form action="" onsubmit="addGroup(event)">
            <input type="number" id="groupAdd" autocomplete="off"/>
            <button>Добавить</button>
        </form>
        <form action="" onsubmit="removeGroup(event)">
            <input type="number" id="groupRemove" autocomplete="off"/>
            <button>Убрать</button>
        </form>
        <ul id='groups' style="list-style: none; padding: 0;">
        </ul>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            
            function addGroup(event) {
                var input = document.getElementById("groupAdd")
                var node = document.createTextNode('group_id = ' + input.value)

                var groups = document.getElementById('groups')
                var group = document.createElement('li')
                group.id = 'gr' + input.value;
                group.appendChild(node)
                groups.appendChild(group)
                
                var info = {
                    action: "add",
                    group_id: input.value,
                };
                
                ws.send(JSON.stringify(info))
                input.value = ''
                event.preventDefault()
            }
            
            function removeGroup(event) {
                var input = document.getElementById("groupRemove")
                
                var groups = document.getElementById('groups')
                var group = document.getElementById('gr' + input.value)
                groups.removeChild(group)
                
                var info = {
                    action: "remove",
                    group_id: input.value,
                };
                ws.send(JSON.stringify(info))
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""