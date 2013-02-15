    recentlyToggled = [] 
    function switchLight(key) {
        active = key.target.classList.contains("active")
        key = key.target.id.replace("switch-","")
        recentlyToggled.push(key)
        // turns a light or fan on / off
        var postdata = {"NOCACHE":"YES"} ;
        if (active){
        $.post('/on/' + key, postdata, function(data) { }  );
        } else {
        $.post('/off/' + key, postdata, function(data) { }  );
        }
       // return false ;
    };

    function updateStates() {
        // checks for config changes and stat changes
        var postdata = {"NOCACHE":"YES"} ;
        $.post('/status', postdata, function (data) {processData(data)});
       // return false ;
    };    
    
    function unlockDoor() {
        // checks for config changes and stat changes
        var postdata = {"NOCACHE":"YES"} ;
        $.post('/unlock/'+ doorLockTimeout.value , postdata, function (data) {changeDoor(data)});
       // return false ;
    };   
    
    
    function changeDoor(){
        doorTimeout = setInterval("resetDoor()",doorLockTimeout.value*1000);
        frontDoor.className = "button-positive";
    }
    
    function resetDoor(){
        frontDoor.className = "button-negative";
        clearInterval(doorTimeout);
    }
    
    
    function processData(data){
    data = jQuery.parseJSON(data);
        for (key in data.description) { 
            if (recentlyToggled.indexOf(key) != -1 ){
                console.log("skipping " + key)
                recentlyToggled.splice(recentlyToggled.indexOf(key))
                break;
            }
            if (document.getElementById("switch-"+key)) {
                existing = document.getElementById("switch-"+key)
                if (data.state[key] == 1){
                    existing.classList.add("active")
                } else {
                    existing.classList.remove("active")
                }
                existing.getElementsByClassName("toggle-handle")[0].style.webkitTransform = ""
            } else {
                a = document.createElement('li')
                a.id="list-switch-" + key
                b = document.createTextNode(data.description[key])
                a.appendChild(b)
                c = document.createElement('div')
                c.classList.add('toggle')
                c.classList.add('lightSwitch')
                c.addEventListener('toggle', switchLight)
                if (data.state[key] == 1){
                    c.classList.add('active')
                }
                c.id="switch-" + key
                d = document.createElement('div')
                d.classList.add("toggle-handle")
                c.appendChild(d)
                a.appendChild(c)
                switches.appendChild(a) 
                }
            }
    }
    
    updateStates();
    
    t=setInterval("updateStates()",750);
new FingerBlast('#switches');