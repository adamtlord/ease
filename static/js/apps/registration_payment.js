$(function() {

    var updatePlanCharges = function() {
        $('#plan_charges').removeClass('plan1 plan2 plan3');
        $('#plan_charges').addClass('plan' + $('input[name=plan]:checked').val());
    };

    var validateCoupon = function() {
        $.ajax({
                url: "/billing/retrieve_coupon/",
                data: {
                    coupon_code: $('#id_coupon').val()
                },
                beforeSend: function() {
                    $('#apply_coupon').addClass('loading');
                    $('#coupon_form_group .help-block').text('');
                }
            })
            .done(function(data) {
                $('#apply_coupon').removeClass('loading');
                if (data.success) {
                    $('#coupon_form_group .help-block').text('Valid coupon!');
                    $('#plan_charges').addClass('coupon').find('.coupon').html('The coupon you entered will reduce your first invoice by $' + parseFloat(data.stripe_coupon.amount_off / 100).toFixed(2));
                } else {
                    $('#coupon_form_group .help-block').text(data.message);
                }
            });
    };

    $("#user_form").submit(function() {

        if ($("#add_card").is(":visible")) {
            var form = this;
            var card = {
                number: $("#credit_card_number").val(),
                expMonth: $("#expiry_month").val(),
                expYear: $("#expiry_year").val(),
                cvc: $("#cvv").val(),
                address_zip: $('#id_billing_zip').val()
            };

            Stripe.createToken(card, function(status, response) {
                if (status === 200) {
                    $("#credit-card-errors").hide();
                    $("#id_last_4_digits").val(response.card.last4);
                    $("#stripe_token").val(response.id);
                    form.submit();
                } else {
                    $("#stripe-error-message").text(response.error.message);
                    $("#credit-card-errors").show();
                    $("#user_submit").attr("disabled", false);
                }
            });

            return false;
        }

        return true;

    });

    $('#apply_coupon').click(function() {
        validateCoupon();
    });
    $('#id_coupon').blur(function() {
        if (this.value.length) {
            validateCoupon();
        }
    });

    $("#change_card").click(function() {
        $("#card_on_file").hide();
        $("#add_card").show();
        $("#credit_card_number").focus();
        return false;
    });
    $("#cancel_change_card").click(function() {
        $("#add_card").hide();
        $("#card_on_file").show();
        return false;
    });
    $("#change_ride_card").click(function() {
        $("#add_ride_card").show();
        $("#add_stripe_customer").val(1);
        $("#id_first_name").focus();
    });
    $("#change_plan").click(function() {
        $("#selected_plan").hide();
        $(".plan-buttons").show();
    });

    $('.cc-mask input').mask('0000-0000-0000-0000');
    $('.zip-mask input').mask('00000-0000');

    $('input[name=plan]').change(function() {
        updatePlanCharges();
    });
    updatePlanCharges();
});