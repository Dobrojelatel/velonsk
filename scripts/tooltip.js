document.onmousemove = moveTip;
function moveTip(e) {
  floatTip = document.getElementById("floatTip");
  floatTipStyle = floatTip.style;
  var w = 300; // Ширина слоя

  // Для браузера IE
  if (document.all) { 
    x = event.x + document.body.scrollLeft; 
    y = event.y + document.body.scrollTop; 

  // Для остальных браузеров
  } else { 
    x = e.pageX; // Координата X курсора
    y = e.pageY; // Координата Y курсора
  }

  // Показывать слой справа от курсора 
  if ((x + w + 10) < document.body.clientWidth) { 
    floatTipStyle.left = x + 'px';

  // Показывать слой слева от курсора
  } else { 
    floatTipStyle.left = x - w + 'px';
  }
  // Положение от верхнего края окна браузера
  floatTipStyle.top = y + 20 + 'px';
}

function toolTip(msg) {
  floatTipStyle = document.getElementById("floatTip").style;
  if (msg) {

    // Выводим  текст подсказки
    document.getElementById("floatTip").innerHTML = msg;
    floatTipStyle.display = "block"; // Показываем слой
  } else { 
    floatTipStyle.display = "none"; // Прячем слой
  } 
}

function AJAXTip(key){
	container = document.getElementById("CONT_"+key);
	if(container){
		document.getElementById("floatTip").style.width = container.style.width;
		toolTip(container.innerHTML);
	}else {
		var container = document.createElement('div');
		container.setAttribute('id',"CONT_"+key);
		container.setAttribute('class','tip');
		container.innerHTML='<center>Loading</center>';
		var body = document.getElementById("content").appendChild(container);
		document.getElementById("floatTip").style.width = "300px";
		toolTip(container.innerHTML);
		
		var req;

		if (window.XMLHttpRequest) req = new XMLHttpRequest(); 
		else if (window.ActiveXObject) {
		    try {
		        req = new ActiveXObject('Msxml2.XMLHTTP');
		    } catch (e){}
		    try {
		    req = new ActiveXObject('Microsoft.XMLHTTP');
		    } catch (e){}
		}

		if (req) {
		    req.onreadystatechange = function() {
		    	if (req.readyState == 4 && req.status == 200)  { 
					container.innerHTML = req.responseText.replace(new RegExp("block",'g'),'none');
					var img=document.getElementById('img_'+key);
					if(img)container.style.width=500 + img.width;
					  else container.style.width=500;
					document.getElementById("floatTip").style.width = container.style.width;
					document.getElementById("floatTip").innerHTML=container.innerHTML;
				}        
		    };
		    req.open("GET", 'http://velonsk.fd0.ru/biker.php?key='+key, true);
		    req.send(null);
		} 
		else alert("Браузер не поддерживает AJAX");
	}
}
function clearAds(){
	ad = document.getElementById('t35ad');
	if(ad)ad.style.display = "none";
}