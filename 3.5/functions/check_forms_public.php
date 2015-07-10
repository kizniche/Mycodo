<?php
//
// Check for form submission and respond
//

// The following form submission(s) can be executed by both users and guests
// Request to generate a graph
if (isset($_POST['Graph'])) {
    setcookie('graph_type', $_POST['graph_type'], time() + (86400 * 10), "/" );
    setcookie('graph_span', $_POST['graph_span'], time() + (86400 * 10), "/" );
    $_COOKIE['graph_type'] = $_POST['graph_type'];
    $_COOKIE['graph_span'] = $_POST['graph_span'];
    set_new_graph_id();
}
?>
