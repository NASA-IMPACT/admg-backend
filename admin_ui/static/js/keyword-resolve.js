$(':radio').mousedown(function(e){
    var $self = $(this);
    if( $self.is(':checked') ){
      var uncheck = function(){
        setTimeout(function(){$self.removeAttr('checked');},0);
      };
      var unbind = function(){
        $self.unbind('mouseup',up);
      };
      var up = function(){
        uncheck();
        unbind();
      };
      $self.bind('mouseup',up);
      $self.one('mouseout', unbind);
    }
  });

$('.icon-radio label').click(function (event) {
    var input = $('input#' + $(this).attr('for'));
  
    if (input.is(':checked')) {
      // Don't allow us to uncheck if was checked on load. This plays on the
      // fact that the checked _attribute_ represents the on load checked state
      // while the checked _prop_ represents the current checked status.
      if (input.attr('checked')) return;
  
      // Prevent HTML from clicking radio
      event.preventDefault();
  
      // Uncheck input
      input.prop('checked', false);
  
      // Set input that was checked on load to checked. We only allow
      // unchecking of items if nothing was checked on load.
      $(input.parent()).children('input[checked]').prop('checked', true);
    }
  })