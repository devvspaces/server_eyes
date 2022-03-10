$(function() {
    "use strict";

	// Code to pause and play loader
	function playLoader(){
		$('#loader_container').addClass('active')
		$('#loader_span').addClass('play')
	}
	function stopLoader(){
		$('#loader_container').removeClass('active')
		$('#loader_span').removeClass('play')
	}


    /*  Codes for alert popup */
    
    function clearAlerts(){
        let alertsContainer = document.querySelectorAll(".alerts-container .alert-pop .close")

        alertsContainer.forEach(i=>{
            i.click()
        })

    }

    function createAlert(message, tag='success'){
        let alertsContainer = $(".alerts-container")

        // Create alert pop up
        let el = document.createElement('div')
        el.className = 'alert-pop alert-theme removed alert alert-{}'.format(tag)
        el.innerHTML = `
        <span class='close'><i class="ti-close"></i></span>

        <p class='popup-message'>{}</p>

        `.format(message)

        alertsContainer.append(el)

        setTimeout(function(){
            el.classList.remove('removed')
        }, 300)

        setClosePopEvent()
    }

    function setClosePopEvent(){
        if ($('.alert-pop .close').length){
            $('.alert-pop .close').click(function(){
                let main = this.parentElement;
                $(main).addClass('removed')
                setTimeout(function(){
                    main.remove()
                }, 1000)
            })
        }
    }

    setClosePopEvent()



    // Adding the format attr to strings
	String.prototype.format = function () {
		var i = 0, args = arguments;
		return this.replace(/{}/g, function () {
		return typeof args[i] != 'undefined' ? args[i++] : '';
		});
	};

	// Codes for ajax setup for get and post requests to backend
	function getCookie(name) {
		let cookieValue = null;
		if (document.cookie && document.cookie !== '') {
			let cookies = document.cookie.split(';');
			for (let i = 0; i < cookies.length; i++) {
				let cookie = jQuery.trim(cookies[i]);
				// Does this cookie string begin with the name we want?
				if (cookie.substring(0, name.length + 1) === (name + '=')) {
					cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
					break;
				}
			}
		}
		return cookieValue;
	}


	let csrftoken = getCookie('csrftoken');


	function csrfSafeMethod(method) {
		// these HTTP methods do not require CSRF protection
		return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
	}



	try{
		$.ajaxSetup({
			beforeSend: function(xhr, settings) {
				if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
					xhr.setRequestHeader("X-CSRFToken", csrftoken);
				}
			}
		});
	} catch(e){
	}


	function submitForm(e) {
		e.preventDefault()
		let form = this
		let formData = $(this).serialize();

		let thisURL = this.action

		// Play loader
		playLoader()

        // Clear alerts
        clearAlerts()
	
		$.ajax({
			method: "POST",
			url: thisURL,
			data: formData,
			success: function (data){
				// Pause loader
				stopLoader()

				// Get the log message
                let message = data['log']

                // Load to dom
                $('.log_sheet p').html(message);

                // Create alert
                createAlert('Logs were pulled successful')
			},
			error: function (jqXHR) {
				console.log(jqXHR)
				// Pause loader
				stopLoader()

				if (jqXHR.status == 403){
					window.location.reload()
				}

                // Create error alert
                createAlert('Error occured while trying to get logs.', 'danger')
			},
		})
	}

	if($('#log_form').length){
		$('#log_form').submit(submitForm);
	}
	
	
});