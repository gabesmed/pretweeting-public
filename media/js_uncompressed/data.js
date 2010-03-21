var fetching_sub_content = false;
var fetching_discovery_content = false;

function show_sub_content(url) {
    if(fetching_sub_content) {
        return;
    }
    $("#sub_loading").show();
    fetching_sub_content = true;
    
    $.ajax({
      url: url,
      type: "GET",
      success: function(html) {
        $("#sub_content").html(html);
        $("#sub_loading").hide();
        fetching_sub_content = false
      },
      error: function() {
        $("#sub_content").html("There was an error loading this page.");
        $("#sub_loading").hide();
        fetching_sub_content = false
      }
    });
}

function show_discovery_content(url, header_id) {
    if(fetching_discovery_content) {
        return;
    }
    $("#discovery_loading").show();
    fetching_discovery_content = true;
    $.ajax({
      url: url,
      type: "GET",
      success: function(html) {
        $("#discovery_content").html(html);
        $("#discovery_loading").hide();
        fetching_discovery_content = false;
        set_discovery_header_link(header_id);
      },
      error: function() {
        fetching_discovery_content = false;
        $("#discovery_loading").hide();
        $("#discovery_content").html("There was an error loading this page.");
      }
    });
}

function set_discovery_header_link(header_id) {
  $("#discovery_header a").removeClass("active");
  $("#discovery_header a#" + header_id).addClass("active");
}

function show_word(word_id) {
    url = "/words/" + word_id;
    show_sub_content(url);
    return false;
}

function show_random() {
    show_sub_content("/words/random");
    return false;
}

function search_word(content) {
    content = content.replace('#', '%23');
    url = "/words/search/" + content;
    show_sub_content(url);
    return false;
}

(function($){
    $.extend($.fn, {
        delayedObserver: function(callback, delay, options){
            return this.each(function(){
                var el = $(this);
                var op = options || {};
                el.data('oldval', el.val())
                    .data('delay', delay || 0.5)
                    .data('condition', op.condition || function() { return ($(this).data('oldval') == $(this).val()); })
                    .data('callback', callback)
                    [(op.event||'keyup')](function(){
                        if (el.data('condition').apply(el)) { return }
                        else {
                            if (el.data('timer')) { clearTimeout(el.data('timer')); }
                            el.data('timer', setTimeout(function(){
                                el.data('callback').apply(el);
                            }, el.data('delay') * 1000));
                            el.data('oldval', el.val());
                        }
                    });
            });
        }
    });
})(jQuery);
