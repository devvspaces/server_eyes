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

	// Custom select box
	$(document).ready(function() {
		$('.cSelect').select2();
	});

	// Event for updating branches on selecting repo
	$('#repo-input-p').on('select2:select', function (e) {
		let data = e.params.data;

		// Get the branches string
    	let branches = data['title']

		// Split to list of branches
		branches = branches.split(',')

		// Clean all option in branch select
		$('#branch-input-p').empty()

		// Loop through to add the branch select
		branches.forEach(branch=>{
			var data = {
				id: branch,
				text: branch
			};
			var newOption = new Option(data.text, data.id, false, false);
			$('#branch-input-p').append(newOption)
		})

		// Update select2
		$('#branch-input-p').trigger('change');
	});

	// Event for updating subdomains on selecting domain
	$('#domain-input-p').on('select2:select', function (e) {
		let data = e.params.data;

		// Get the subdomains string
    	let subdomains = data['title']
		let domain_link_name = data['text']

		// Split to list of subdomains
		subdomains = subdomains.split('?')

		// Clean all option in subdomains select
		$('#subdomain-input-p').empty()

		// Add default data to the select
		var newOption = new Option('-Choose a Subdomain-', '', false, false);
		$('#subdomain-input-p').append(newOption)

		// Loop through to add the subdomains select
		subdomains.forEach(subdomain=>{
			// Split subdomain to domain link and record id
			let [domain_link, record_id] = subdomain.split('*')
			var data = {
				id: record_id,
				text: domain_link
			};
			var newOption = new Option(data.text, data.id, false, false);
			$('#subdomain-input-p').append(newOption)
		})

		// Update select2
		$('#subdomain-input-p').trigger('change');

		// Update the subdomain-input-new under the select
		$('#subdomain-input-new .input-group-text').text('.'+domain_link_name)
	});


	// Code for new and select subdomain
	if ($('#new-subdomain-form-btn').length){
		$('#new-subdomain-form-btn').click(function(e){
			// Toggle items visibility
			$('#subdomain-input-new').removeClass('d-none')
			$('#subdomain-input-p').next().addClass('d-none')

			// Btns
			$('#new-subdomain-form-btn').addClass('d-none')
			$('#select-subdomain-form-btn').removeClass('d-none')

			// Update select2
			$('#subdomain-input-p').val('').trigger('change');
		})
	}
	if ($('#select-subdomain-form-btn').length){
		$('#select-subdomain-form-btn').click(function(e){
			// Toggle items visibility
			$('#subdomain-input-new').addClass('d-none')
			$('#subdomain-input-p').next().removeClass('d-none')

			// Btns
			$('#new-subdomain-form-btn').removeClass('d-none')
			$('#select-subdomain-form-btn').addClass('d-none')
		})
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
                createAlert('Logs were pulled successfully')
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

	function submitAddSubdomainForm(e) {
		e.preventDefault()
		let form = this
		let formData = $(this).serialize();

		let thisURL = this.action

		// Play loader
		playLoader()

        // Clear alerts
        clearAlerts()

		// Get success and error text if there
		let success_text = $(form).attr('success_text')
		let error_text = $(form).attr('error_text')
	
		$.ajax({
			method: "POST",
			url: thisURL,
			data: formData,
			success: function (data){
				// Pause loader
				stopLoader()

                // Create alert
				if (success_text){
					createAlert(success_text)
				} else {
					createAlert('New subdomain created successfully, reloading page now.')
				}
                

				// Reload site after 3 seconds
				let reload_time = 1000 * 3;
				setTimeout(function(){
					location.reload()
				}, reload_time)
			},
			error: function (jqXHR) {
				console.log(jqXHR)
				let data = jqXHR['responseJSON']
				// Pause loader
				stopLoader()

				// Check if there are errors
                let errors = data['errors']

				console.log(errors)

                if (errors){
                    $('.form-errors').html('');
                    for (const [key, value] of Object.entries(errors)) {
						let field = value['field']
						let reason = value['reason']
                        if (field != '__all__'){
                            let input = form.querySelector("[name='" + field + "']")
                            let new_el = document.createElement('small')
                            new_el.classList.add('text-danger')
                            new_el.innerText = reason

							let form_error_div;
                            
                            // Get the form error div
							if (input.parentElement.classList.contains('input-group')){
								form_error_div = input.parentElement.parentElement.querySelector('.form-errors')
							} else {
								form_error_div = input.parentElement.querySelector('.form-errors')
							}
                            
                            form_error_div.appendChild(new_el)
                        }
                    }
                }

                // Create error alert
				if (error_text){
					createAlert(error_text, 'danger')
				} else {
					createAlert('Error occured while trying to create domain, check errors.', 'danger')
				}
                
			},
		})
	}

	if($('#add-subdomain-form').length){
		$('#add-subdomain-form').submit(submitAddSubdomainForm);
	}

	if($('#deploy-react-form').length){
		$('#deploy-react-form').submit(submitAddSubdomainForm);
	}
	
	
});