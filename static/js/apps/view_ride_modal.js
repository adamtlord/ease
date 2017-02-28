 /* global confirm */

 $(function(){
    $('#viewRideModal').on('show.bs.modal', function (e) {
        var rideID = $(e.relatedTarget).data('rideid');
        var modal = $(this).find('.modal-content');
        $.get('/concierge/ride/'+rideID+'/detail-modal/', function(response){
            modal.html(response);
        });
    });
    $('.btn.cancel-ride').on('click', function() {
        return confirm('Are you sure you want to cancel and permanently delete this ride?');
    });
});