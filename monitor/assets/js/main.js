$(function() {
    "use strict";

	// Always select theme to use
	let seleteTheme = () => {
		$("body").append('');
		var boxed = "";
		if ($(".page-wrapper").hasClass("box-layout")) {
			boxed = "box-layout";
		}
		$(".page-wrapper").attr("class", "page-wrapper compact-wrapper " + boxed);
		localStorage.setItem('page-wrapper', 'compact-wrapper');
	}
	seleteTheme()

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


	function timeRedirect(time=3, redirect=''){
		// Reload site after 3 seconds
		let reload_time = 1000 * time;
		setTimeout(function(){
			if (redirect !== undefined && redirect !== null && (redirect.length > 0)){
				location.href = redirect;
			} else {
				location.reload();
			}
		}, reload_time)
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

		$('.form-errors').html('');
	
		$.ajax({
			method: "POST",
			url: thisURL,
			data: formData,
			success: function (data){
				// Pause loader
				stopLoader()
				
				// NOTE: Remove this in production
				console.log(data)

				// Get the log message
                let message = data['log']

                // Load to dom
                $('.log_sheet p').html(message);

                // Create alert
                createAlert('Logs were pulled successfully')
			},
			error: function (jqXHR) {
				// Pause loader
				stopLoader()

				if (jqXHR.status == 403){
					window.location.reload()
				}

                // Create error alert
                createAlert('Error occured while trying to get logs.', 'danger')

				let data = jqXHR['responseJSON'];

				// Remove this in production
                console.log(data)

                // Check if there are errors
                let errors = data['errors']

                if (errors){
                    for (const [key, value] of Object.entries(errors)) {
                        if (key != '__all__'){
                            let input = form.querySelector(".ajax-input[name='" + key + "']")
                            let new_el = document.createElement('small')
                            new_el.classList.add('text-danger')
                            new_el.innerText = value
                            
                            // Get the form error div
                            let form_error_div = document.querySelector(`div[for='${input.id}']`)
                            form_error_div.appendChild(new_el)
                        }
                    }
                }
			},
		})
	}

	if($('#log_form').length){
		$('.log_sheet p').html('')
		$('#log_form').submit(submitForm);
	}

	function submitAddSubdomainForm(e) {
		e.preventDefault()
		let form = this
		console.log('What is this')
		console.log(this)
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
				stopLoader()
				let message = data['message']
				if (message){
					success_text = message
				}
				createAlert(success_text)

				console.log(data)
				timeRedirect(3, data['redirect'])
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

				let message = data['message']
				if (message){
					error_text = message
				}
				createAlert(error_text, 'danger')
                
			},
		})
	}


	if($('#add-subdomain-form').length){
		$('#add-subdomain-form').submit(submitAddSubdomainForm);
	}
	if($('.record_update_modal').length){
		$('.record_update_modal').submit(submitAddSubdomainForm);
	}
	if($('.subdomain-delete-form').length){
		$('.subdomain-delete-form').submit(function(e){
			let form = this
			e.preventDefault()
			swal({
				title: "Are you sure you want to delete this subdomain?",
				text: "Once deleted, you will not be able to recover this record, you will have to create it again!",
				icon: "warning",
				buttons: true,
				dangerMode: true,
			})
			.then((willDelete) => {
				if (willDelete) {
					let formData = $(form).serialize();
					let thisURL = form.action
			
					playLoader()
					clearAlerts()
					$.ajax({
						method: "POST",
						url: thisURL,
						data: formData,
						success: function (data){
							console.log(data)
							stopLoader()
							let message = data['message']
							swal(message, {
								icon: "success",
							});
							timeRedirect(3, data['redirect'])

						},
						error: function (jqXHR) {
							console.log(jqXHR)
							let data = jqXHR['responseJSON']
							console.log(data)
							stopLoader()
							let message = data['message']
							createAlert(message, 'danger')
						},
					})
				} else {
					swal("Your subdomain is safe!");
				}
			})
		});
	}

	if($('#deploy-react-form').length){
		$('#deploy-react-form').submit(submitAddSubdomainForm);
	}


	if ($('#logModalContent').length){
		// For getting logs on app page
		var logModalContent = document.getElementById('logModalContent')

		// Get log url
		let log_url = $('#logModalContent').attr('log')

		logModalContent.addEventListener('show.bs.modal', function (event) {
			// Play loader
			playLoader()

			// Clear alerts
			clearAlerts()

			// Get success and error text if there
			let success_text = 'Logs are gotten successfully'
			let error_text = 'Error while getting logs'
		
			$.ajax({
				method: "GET",
				url: log_url,
				success: function (data){
					// Pause loader
					stopLoader()

					// Create alert
					createAlert(success_text)

					// Load result into modal
					let text = data['data'];
					$('#logModalContent p.content').html(text)

					setTimeout(function(){
						clearAlerts()
					}, 5000)

				},
				error: function (jqXHR) {
					// Pause loader
					stopLoader()

					// Create error alert
					createAlert(error_text, 'danger')
					
				},
			})
		
		})


		function clearLogs(event) {
			event.preventDefault()

			let formData = $(this).serialize();
			
			// Play loader
			playLoader()

			// Clear alerts
			clearAlerts()

			let error_text = 'Error while clearing logs'
			let success_text = 'Logs cleared successfully'
		
			$.ajax({
				method: "POST",
				url: log_url,
				data: formData,
				success: function (data){
					// Pause loader
					stopLoader()

					// Create alert
					createAlert(success_text)

					// Set result into modal
					let text = 'No logs yet';

					$('#logModalContent p.content').html(text)

				},
				error: function (jqXHR) {
					// Pause loader
					stopLoader()

					// Create error alert
					createAlert(error_text, 'danger')
					
				},
			})
		
		}

		let logForm = document.querySelector('#logModalContent form')
		logForm.addEventListener('submit', clearLogs)
	}
	
	

	if ($('.are-you-sure-delete').length){
		$('.are-you-sure-delete').click(function(e){
			e.preventDefault()

			let value = confirm("Are you sure you want to perform this account?");
			if (value){
				location.href = $(this).attr('href')
			}
		})
	}
	
});