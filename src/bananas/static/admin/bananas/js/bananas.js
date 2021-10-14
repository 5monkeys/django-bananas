(function() {
  var $ = window.django.jQuery;
  var $document = $(document);
  var $html = $("html");
  var $searchbars = $("input[name=q]");

  var SIDEBAR_TRANSITION_DURATION = parseInt(
    window
      .getComputedStyle($html[0])
      .getPropertyValue("--sidebar-transition-duration"),
    10
  ); // ms

  polyfillWindowScrollProperties();
  markCurrentSidebarLink();
  setupSidebar();

  function markCurrentSidebarLink() {
    var navLinks = Array.prototype.slice.call(
      document.querySelectorAll("#header nav a")
    );

    var matching = navLinks
      .map(function(link, index) {
        return {
          element: link,
          match:
            link.origin === window.location.origin
              ? matchPath(window.location.pathname, link.pathname)
              : 0,
          index: index,
        };
      })
      .filter(function(item) {
        return item.match > 0;
      })
      .sort(function(a, b) {
        return b.match - a.match || a.index - b.index;
      });

    if (matching.length > 0) {
      var bestMatchingLink = matching[0].element;
      //bestMatchingLink.className += " is-selected";
      //document.location.hash = bestMatchingLink.name;
    }

    var $filteredNavItem = $('.filtered nav a.is-selected')[0];
    if ($filteredNavItem) {
      document.location.hash = $filteredNavItem.name;
    }
  }

  function matchPath(currentPath, linkPath) {
    var currentParts = currentPath.split("/");
    var linkParts = linkPath.split("/");
    var length = Math.min(currentParts.length, linkParts.length);
    var index = 0;
    for (; index < length; index++) {
      if (currentParts[index] !== linkParts[index]) {
        return index;
      }
    }
    return index;
  }

  function setupSidebar() {
    $document.on("click", "#header nav a", function() {
      if ($html.hasClass("is-sidebarOpen")) {
        closeSidebar();
      }
    });

    $document.on("click", ".hamburger", function() {
      if ($html.hasClass("is-sidebarOpen")) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });

    $document.on("keydown", function(event) {
      if (
        event.keyCode === 27 && // Escape.
        $html.hasClass("is-sidebarOpen")
      ) {
        closeSidebar();
      }
    });

    $document.on("mousedown touchstart", function(event) {
      var $target = $(event.target);
      if (
        $html.hasClass("is-sidebarOpen") &&
        $target.closest("#header").length === 0 &&
        !$target.hasClass(".hamburger") &&
        $target.closest(".hamburger").length === 0
      ) {
        closeSidebar();
      }
    });

    var $submit = $searchbars.siblings("[type=submit]");
    var verbose_name_plural = $("#title").attr("title");
    var objects = verbose_name_plural
        ? ' ' + verbose_name_plural.toLowerCase()
        : '';
    $searchbars.attr(
      'placeholder',
      $submit.val() + objects + ' ...'
    );
  }

  function openSidebar() {
    lockPageScroll();
    $html.addClass("is-sidebarOpen");
    accessibilityFocus($html.find("#header").eq(0));
  }

  function closeSidebar() {
    $html.removeClass("is-sidebarOpen");
    focusContent();
    window.setTimeout(function() {
      unlockPageScroll();
    }, SIDEBAR_TRANSITION_DURATION);
  }

  function focusContent() {
    accessibilityFocus($("main"));
  }

  function polyfillWindowScrollProperties() {
    Object.defineProperties(window, {
      scrollX: {
        get: function() {
          return window.pageXOffset;
        },
      },
      scrollY: {
        get: function() {
          return window.pageYOffset;
        },
      },
    });
  }

  function lockPageScroll() {
    $html.css({
      position: "fixed",
      top: -window.scrollY,
      left: -window.scrollX,
      width: "100%",
    });
  }

  function unlockPageScroll() {
    var left = $html.css("left");
    var top = $html.css("top");
    var leftNum = parseInt(left || "", 10);
    var topNum = parseInt(top || "", 10);
    var scrollX = isFinite(leftNum) ? Math.abs(leftNum) : window.scrollX;
    var scrollY = isFinite(topNum) ? Math.abs(topNum) : window.scrollY;

    $html.css({
      position: "",
      top: "",
      left: "",
      width: "",
      "overflow-y": "",
    });

    window.scrollTo(scrollX, scrollY);
  }

  function accessibilityFocus($element) {
    var scrollX = window.scrollX;
    var scrollY = window.scrollY;
    var originalTabindex = $element.attr("tabindex");
    $element
      .attr("tabindex", -1)
      .focus()
      .attr("tabindex", originalTabindex);
    window.scrollTo(scrollX, scrollY);
  }
})();
