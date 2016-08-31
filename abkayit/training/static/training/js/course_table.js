$(document).ready(function(){
    $('[data-id="course_table"]').DataTable({
            "dom": 'Bfrtip',
            "language": {
                    "url": "/static/base/Turkish.json"
            },
            "searching": true,
            "bJQueryUI": false,
            "ordering": true,
            "paging" : false,
            buttons : [
              'copyHtml5',
              'excelHtml5',
              'csvHtml5',
              'pdfHtml5'
            ],
    });
    $('#course_table tbody tr').click(function(){
		var attr = 	$(this).attr('href');
		if (typeof attr !== typeof undefined && attr !== false) {
			window.location=attr;
		}
	});
});