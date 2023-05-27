var ADDR;
function SetAddr(addr)
{
    console.log(addr)
    ADDR=addr;
}
function IncrBomb(bool)
{
    fetch(ADDR, {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({ "IncDecBomb": bool})
        })
        .then(response =>  response.json())
        .then(data => 
        {
            console.log("OK")
        })
        .catch(error => {
            console.log("Error:",error)
        });
}
function IncrValve(bool)
{
    console.log(bool)
    fetch(ADDR, {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({ "IncDecValve": bool})
        })
        .then(response =>  console.log("OK"))
        .catch(error => {
            console.log("Error:",error)
        });
}


function GetData()
{
    fetch(ADDR, {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            //"X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ "GetData": true})
        })
        .then(response =>  response.json())
        .then(data => 
        {
            if( data.NoActive == true)
            {
                document.getElementById("IDCardBody").setAttribute("class","card-body text-danger");
                document.getElementById("DivIDLevel").innerHTML="-";
                document.getElementById("DivIDCistern").innerHTML="-";
                document.getElementById("DivIDValve").innerHTML="-";
                document.getElementById("DivIDBomb").innerHTML="-";
            }
            else
            {
                //document.getElementById("DivID").innerHTML="";
                if (data.error==false)
                    document.getElementById("DivID").innerHTML=data.error; 
                else
                    document.getElementById("DivID").innerHTML="";
                document.getElementById("DivIDLevel").innerHTML=data.level;
                document.getElementById("DivIDCistern").innerHTML=data.cistern;
                document.getElementById("DivIDValve").innerHTML=data.valve;
                document.getElementById("DivIDBomb").innerHTML=data.bomb;
                setTimeout(GetData,2000);
            }
        })
        .catch(error => {
            console.log("Error:",error)
        
            document.getElementById("DivID").innerHTML=error;
            //alert(error)
        });
}
// function getCookie(name)
// {
//     let cookieValue = null;
//     if (document.cookie && document.cookie !== "") {
//         const cookies = document.cookie.split(";");
//         for (let i = 0; i < cookies.length; i++) {
//         const cookie = cookies[i].trim();
//         if (cookie.substring(0, name.length + 1) === (name + "=")) {
//             cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//             break;
//         }
//         }
//     }
//     return cookieValue;
// }