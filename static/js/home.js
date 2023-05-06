var ADDR;
function SetAddr(addr)
{
    console.log(addr)
    ADDR=addr;
}
function BtnActDesact()
{
    fetch(ADDR, {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ "BtnActDesact": true})
        })
        .then(response => response.text())
        .then(data => 
        {
            if( data == "OK_A")
            {
                GetData();
                document.getElementById("IdBtnActDesact").innerHTML="Desactivar"
                document.getElementById("IdBtnActDesact").setAttribute("class","btn btn-danger")
            }
            else if ( data == "OK_D")
            {
                GetData();
                document.getElementById("IdBtnActDesact").innerHTML="Activar"
                document.getElementById("IdBtnActDesact").setAttribute("class","btn btn-success")
            }
            else
                document.getElementById("DivID").innerHTML="Error al Activar";
        })
        .catch(error => {
            console.log("Error:",error) 
            alert("Error Conectar con el Servidor",error)
            document.getElementById("DivID").innerHTML="Error Conectar con el Servidor";
            document.getElementById("IdBtnActDesact").innerHTML="Activar"
            document.getElementById("IdBtnActDesact").setAttribute("class","btn btn-success")
        });
}



function GetData()
{
    fetch(ADDR, {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ "GetData": true})
        })
        .then(response => response.text())
        .then(data => 
        {
            if( data == "NoActive")
                document.getElementById("DivID").innerHTML="Thread no Activo"
            else
            {
                document.getElementById("DivID").innerHTML=data
                setTimeout(GetData,2000);
            }
        })
        .catch(error => {
            console.log("Error:",error)
            alert(error)
        });
}
function getCookie(name)
{
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + "=")) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
        }
        }
    }
    return cookieValue;
}