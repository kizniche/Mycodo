<?php
/**
 * Class OneFileLoginApplication
 *
 * An entire php application with user registration, login and logout in one file.
 * Uses very modern password hashing via the PHP 5.5 password hashing functions.
 * This project includes a compatibility file to make these functions available in PHP 5.3.7+ and PHP 5.4+.
 *
 * @author Panique
 * @link https://github.com/panique/php-login-one-file/
 * @license http://opensource.org/licenses/MIT MIT License
 */


if (isset($_COOKIE['debug']) && $_COOKIE['debug'] == True) {
    ini_set('display_errors', 'On');
    error_reporting(E_ALL);
}

// Security Measures
// Set utf-8 character set
header('charset=utf-8');
// Prevents javascript XSS attacks aimed to steal the session ID
ini_set('session.cookie_httponly', 1);
// // Session ID cannot be passed through URLs
ini_set('session.use_only_cookies', 1);
// // Uses a secure connection (HTTPS) if possible
ini_set('session.cookie_secure', 1);

function start_profiler() {
    declare(ticks=1);
    require_once('./classes/SimpleProfiler.php');
    SimpleProfiler::start_profile();
}

if (isset($_POST['debug'])) {
    if ($_POST['debug'] == 1) {
        setcookie('debug', True, time() + (86400 * 10), "/" );
        $_COOKIE['debug'] = True;
        start_profiler();
    } else {
        setcookie('debug', False, time() + (86400 * 10), "/" );
        $_COOKIE['debug'] = False;
    }
} else if (isset($_COOKIE['debug'])) {
    if ($_COOKIE['debug'] == True) {
        start_profiler();
    } else $debug = False;
} else {
    setcookie('debug', False, time() + (86400 * 10), "/" );
    $_COOKIE['debug'] = False;
}

class OneFileLoginApplication {
    // @var string Type of database used
    private $db_type = "sqlite"; //

    // @var string Path of the database file
    private $db_sqlite_path = "../config/users.db";

    // @var object Database connection
    private $db_connection = null;

    // @var bool Login status of user
    private $user_is_logged_in = false;

    // @var string System messages, likes errors, notices, etc.
    public $feedback = "";


    // Checks for PHP version and PHP password compatibility library and runs the application
    public function __construct() {
        if ($this->performMinimumRequirementsCheck()) {
            $this->runApplication();
        }
    }

    /**
     * Performs a check for minimum requirements to run this application.
     * Does not run the further application when PHP version is lower than 5.3.7
     * Does include the PHP password compatibility library when PHP version lower than 5.5.0
     * (this library adds the PHP 5.5 password hashing functions to older versions of PHP)
     * @return bool Success status of minimum requirements check, default is false
     */
    private function performMinimumRequirementsCheck() {
        if (version_compare(PHP_VERSION, '5.3.7', '<')) {
            echo "Sorry, Simple PHP Login does not run on a PHP version older than 5.3.7 !";
        } elseif (version_compare(PHP_VERSION, '5.5.0', '<')) {
            require_once("libraries/password_compatibility_library.php");
            return true;
        } elseif (version_compare(PHP_VERSION, '5.5.0', '>=')) {
            return true;
        }
        // default return
        return false;
    }

    // controller that handles the entire flow of the application.
    public function runApplication() {
        if (!file_exists($this->db_sqlite_path)) exit("User database does not exist. Run 'sudo update-database.py -i' from the install directory to create required database.");
        
        if (isset($_POST["register"])) {
            if ($this->checkRegistrationData()) {
                if ($this->createDatabaseConnection()) {
                    $this->createNewUser();
                }
            }
        } else if (isset($_POST["deleteuser"])) {
            if ($this->checkDeleteUserData()) {
                if ($this->createDatabaseConnection()) {
                    $this->deleteUser();
                }
            }
        } else if (isset($_POST['edituser'])) {
            $this->createDatabaseConnection();
            $sql = 'SELECT user_password_hash, user_restriction
                    FROM users
                    WHERE user_name = :user_name
                    LIMIT 1';
            $query = $this->db_connection->prepare($sql);
            $query->bindValue(':user_name', $_COOKIE['login_user']);
            $query->execute();
            $result_row = $query->fetchObject();
            $current_user_hash = $result_row->user_password_hash;
            $current_user_restriction = $result_row->user_restriction;
            $authorized = false;
            if ($current_user_hash == $_COOKIE['login_hash'] && ($current_user_restriction == 'admin' || $_COOKIE['login_user'] == $_POST['user_name'])) {
                $authorized = true;
            }
            if ($authorized) {
                $sql = 'SELECT user_name, user_password_hash, user_email, user_restriction, user_theme
                        FROM users
                        WHERE user_name = :user_name
                        LIMIT 1';
                $query = $this->db_connection->prepare($sql);
                $query->bindValue(':user_name', $_POST['user_name']);
                $query->execute();
                $result_row = $query->fetchObject();
                $edit_user_name = $result_row->user_name;
                $edit_password_hash = $result_row->user_password_hash;
                $edit_user_email = $result_row->user_email;
                $edit_user_restriction = $result_row->user_restriction;
                $edit_user_theme = $result_row->user_theme;
                if (htmlentities($_POST['user_email'], ENT_QUOTES) != $edit_user_email) {
                    if ($this->checkEmailChangeData()) {
                        $this->changeEmail();
                    }
                }
                if (strcmp(htmlentities($_POST['user_restriction'], ENT_QUOTES), $edit_user_restriction) && $current_user_restriction == 'admin') {
                    $this->changeRestriction();
                }
                if (strcmp(htmlentities($_POST['user_theme'], ENT_QUOTES), $edit_user_theme)) {
                    $this->changeTheme();
                }
                if (htmlentities($_POST['new_password'], ENT_QUOTES) != '' && (password_hash(htmlentities($_POST['new_password'], ENT_QUOTES), PASSWORD_DEFAULT) != $edit_password_hash)) {
                    if ($this->checkPasswordChangeData()) {
                        $this->changePassword();
                    }
                }
            }
        }

        // start the session (required)
        $this->doStartSession();
        // check for possible user interactions (login with cookie/session/post data or logout)
        $this->performUserLoginAction();
        // show page based on user's login status
        if ($this->getUserLoginStatus()) {
            $this->showPageLoggedIn();
        } else {
            $this->showPageLoginForm();
        }
    }

    /**
     * Creates a PDO database connection (in this case to a SQLite flat-file database)
     * @return bool Database creation success status, false by default
     */
    private function createDatabaseConnection() {
        try {
            $this->db_connection = new PDO($this->db_type . ':' . $this->db_sqlite_path);
            return true;
        } catch (PDOException $e) {
            $this->feedback = "PDO database connection problem: " . $e->getMessage();
        } catch (Exception $e) {
            $this->feedback = "General problem: " . $e->getMessage();
        }
        return false;
    }

    // Handles the flow of the login/logout process.
    private function performUserLoginAction() {
        if (isset($_GET["action"]) && $_GET["action"] == "logout") {
            $this->doLogout();
        } elseif (isset($_COOKIE['login_user'])) {
            // remember: the user can log in with username or email address
            $this->createDatabaseConnection();
            $sql = 'SELECT user_name, user_email, user_password_hash
                    FROM users
                    WHERE user_name = :user_name OR user_email = :user_name
                    LIMIT 1';
            $query = $this->db_connection->prepare($sql);
            $query->bindValue(':user_name', $_COOKIE['login_user']);
            $query->execute();
            $result_row = $query->fetchObject();
            if ($_COOKIE['login_hash'] == $result_row->user_password_hash) {
                $_SESSION['user_name'] = $result_row->user_name;
                $_SESSION['user_email'] = $result_row->user_email;
                $_SESSION['user_is_logged_in'] = true;
                $this->doLoginWithCookieData();
            } else {
                $this->feedback = "Invalid cookie data.";
                return false;
            }
        } elseif (isset($_POST["login"])) {
            $this->doLoginWithPostData();
        }
    }

    // Start the session.
    private function doStartSession() {
        session_start();
    }

    // Process flow with cookie data
    private function doLoginWithCookieData() {
        $this->user_is_logged_in = true;
    }

    // Process flow of login with POST data
    private function doLoginWithPostData() {
        if ($this->checkLoginFormDataNotEmpty()) {
            if ($this->createDatabaseConnection()) {
                $this->checkPasswordCorrectnessAndLogin();
            }
        }
    }

    // Logs the user out
    private function doLogout() {
        $_SESSION = array();
        setcookie("login_user", "", time() - 3600, '/');
        setcookie("login_hash", "", time() - 3600, '/');
        unset($_COOKIE['login_user']);
        unset($_COOKIE['login_hash']);
        $this->user_is_logged_in = false;
        $this->feedback = "Successfully logged out.";
    }

    /**
     * Validates the login form data, checks if username and password are provided
     * @return bool Login form data check success state
     */
    private function checkLoginFormDataNotEmpty()
    {
        if (!empty($_POST['user_name']) && !empty($_POST['user_password'])) {
            return true;
        } elseif (empty($_POST['user_name'])) {
            $this->feedback = "Username field was empty.";
        } elseif (empty($_POST['user_password'])) {
            $this->feedback = "Password field was empty.";
        }
        return false;
    }

    /**
     * Checks if user exits, if so: check if provided password matches the one in the database
     * @return bool User login success status
     */
    private function checkPasswordCorrectnessAndLogin() {
        $sql = 'SELECT user_name, user_email, user_password_hash
                FROM users
                WHERE user_name = :user_name OR user_email = :user_name
                LIMIT 1';
        $query = $this->db_connection->prepare($sql);
        $query->bindValue(':user_name', $_POST['user_name']);
        $query->execute();
        $result_row = $query->fetchObject();
        if ($result_row) {
            // using PHP 5.5's password_verify() function to check password
            if (password_verify($_POST['user_password'], $result_row->user_password_hash)) {
                if (isset($_POST['cookie'])) {
                    if ($_POST['cookie'] == 1) {
                        // make cookies, expire in 30 days
                        setcookie('login_user', $result_row->user_name, time() + (86400 * 30), "/");
                        setcookie('login_hash', $result_row->user_password_hash, time() + (86400 * 30), "/");
                    }
                } else {
                    // make cookies, expire when browser closed
                    setcookie('login_user', $result_row->user_name, 0, "/");
                    setcookie('login_hash', $result_row->user_password_hash, 0, "/");
                }
                // write user data into PHP SESSION [a file on your server]
                $_SESSION['user_name'] = $result_row->user_name;
                $_SESSION['user_email'] = $result_row->user_email;
                $_SESSION['user_is_logged_in'] = true;
                $this->user_is_logged_in = true;
                $this->writeAuthLog(1, $_POST['user_name']);
                return true;
            } else {
                $this->feedback = "Invalid user or password.";
                $this->writeAuthLog(0, $_POST['user_name']);
            }
        } else {
            $this->feedback = "Invalid user or password.";
            $this->writeAuthLog(2, $_POST['user_name']);
        }
        return false;
    }

    /**
     * Returns the current status of the user's login
     * @return bool User's login status
     */
    public function getUserLoginStatus() {
        return $this->user_is_logged_in;
    }

    // Validate the input
    private function checkRegistrationData() {
        if (!empty($_POST['user_name'])
            && strlen($_POST['user_name']) <= 64
            && strlen($_POST['user_name']) >= 2
            && preg_match('/^[a-z\d]{2,64}$/i', $_POST['user_name'])
            && !empty($_POST['user_email'])
            && strlen($_POST['user_email']) <= 64
            && filter_var($_POST['user_email'], FILTER_VALIDATE_EMAIL)
            && !empty($_POST['user_password_new'])
            && !empty($_POST['user_password_repeat'])
            && ($_POST['user_password_new'] === $_POST['user_password_repeat'])
        ) {
            // only this case return true, only this case is valid
            return true;
        } elseif (empty($_POST['user_name'])) {
            $this->feedback = "Empty Username";
        } elseif (empty($_POST['user_password_new']) || empty($_POST['user_password_repeat'])) {
            $this->feedback = "Empty Password";
        } elseif ($_POST['user_password_new'] !== $_POST['user_password_repeat']) {
            $this->feedback = "Password and password repeat are not the same";
        } elseif (strlen($_POST['user_password_new']) < 6) {
            $this->feedback = "Password has a minimum length of 6 characters";
        } elseif (strlen($_POST['user_name']) > 64 || strlen($_POST['user_name']) < 2) {
            $this->feedback = "Username cannot be shorter than 2 or longer than 64 characters";
        } elseif (!preg_match('/^[a-z\d]{2,64}$/i', $_POST['user_name'])) {
            $this->feedback = "Username does not fit the name scheme: only a-Z and numbers are allowed, 2 to 64 characters";
        } elseif (empty($_POST['user_email'])) {
            $this->feedback = "Email cannot be empty";
        } elseif (strlen($_POST['user_email']) > 64) {
            $this->feedback = "Email cannot be longer than 64 characters";
        } elseif (!filter_var($_POST['user_email'], FILTER_VALIDATE_EMAIL)) {
            $this->feedback = "Your email address is not in a valid email format";
        } else {
            $this->feedback = "An unknown error occurred.";
        }
        return false;
    }

    private function createNewUser() {
        // remove html code etc. from username and email
        $user_name = htmlentities($_POST['user_name'], ENT_QUOTES);
        $user_email = htmlentities($_POST['user_email'], ENT_QUOTES);
        $user_restriction = htmlentities($_POST['user_restriction'], ENT_QUOTES);
        $user_password = $_POST['user_password_new'];
        // Encrypt the user's password with the PHP 5.5's password_hash() function, results in a 60 char hash string.
        // the constant PASSWORD_DEFAULT comes from PHP 5.5 or the password_compatibility_library
        $user_password_hash = password_hash($user_password, PASSWORD_DEFAULT);

        $sql = 'SELECT * FROM users WHERE user_name = :user_name OR user_email = :user_email';
        $query = $this->db_connection->prepare($sql);
        $query->bindValue(':user_name', $user_name);
        $query->bindValue(':user_email', $user_email);
        $query->execute();

        $result_row = $query->fetchObject();
        if ($result_row) {
            $this->feedback = "Sorry, that username / email is already taken. Please choose another one.";
        } else {
            $sql = 'INSERT INTO users (user_name, user_password_hash, user_email, user_restriction, user_theme)
                    VALUES(:user_name, :user_password_hash, :user_email, :user_restriction, :user_theme)';
            $query = $this->db_connection->prepare($sql);
            $query->bindValue(':user_name', $user_name);
            $query->bindValue(':user_password_hash', $user_password_hash);
            $query->bindValue(':user_email', $user_email);
            $query->bindValue(':user_restriction', $user_restriction);
            $query->bindValue(':user_theme', 'light');
            $registration_success_state = $query->execute();
            if ($registration_success_state) {
                $this->feedback = "User " . $user_name . " successfully created.";
                return true;
            } else {
                $this->feedback = "Registration failed.";
            }
        }
        return false;
    }


    private function checkEmailChangeData() {
        if (!empty($_POST['user_name'])
            && strlen($_POST['user_name']) <= 64
            && strlen($_POST['user_name']) >= 2
            && preg_match('/^[a-z\d]{2,64}$/i', $_POST['user_name'])
            && !empty($_POST['user_email'])
            && strlen($_POST['user_email']) <= 64
            && filter_var($_POST['user_email'], FILTER_VALIDATE_EMAIL)
        ) {
            // only this case return true, only this case is valid
            return true;
        } elseif (empty($_POST['user_name'])) {
            $this->feedback = "Empty Username";
        } elseif (strlen($_POST['user_name']) > 64 || strlen($_POST['user_name']) < 2) {
            $this->feedback = "Username cannot be shorter than 2 or longer than 64 characters";
        } elseif (!preg_match('/^[a-z\d]{2,64}$/i', $_POST['user_name'])) {
            $this->feedback = "Username does not fit the name scheme: only a-Z and numbers are allowed, 2 to 64 characters";
        } elseif (empty($_POST['user_email'])) {
            $this->feedback = "Email cannot be empty";
        } elseif (strlen($_POST['user_email']) > 64) {
            $this->feedback = "Email cannot be longer than 64 characters";
        } elseif (!filter_var($_POST['user_email'], FILTER_VALIDATE_EMAIL)) {
            $this->feedback = "Your email address is not in a valid email format";
        } else {
            $this->feedback = "An unknown error occurred.";
        }
        return false;
    }

    private function changeEmail() {
        $user_name = htmlentities($_POST['user_name'], ENT_QUOTES);
        $user_email = htmlentities($_POST['user_email'], ENT_QUOTES);
        $sql = 'UPDATE users SET user_email = :user_email WHERE user_name = :user_name';
        $query = $this->db_connection->prepare($sql);
        $query->bindValue(':user_name', $user_name);
        $query->bindValue(':user_email', $user_email);
        $change_success_state = $query->execute();
        if ($change_success_state) {
            $data_error = "Email change success. ";
            return true;
        } else {
            $data_error = "Email chage failed. ";
        }
        return false;
    }

    private function checkPasswordChangeData() {
        if (!empty($_POST['user_name'])
            && strlen($_POST['user_name']) <= 64
            && strlen($_POST['user_name']) >= 2
            && !empty($_POST['new_password'])
            && !empty($_POST['new_password_repeat'])
            && ($_POST['new_password'] === $_POST['new_password_repeat'])
        ) {
            return true;
        } elseif (empty($_POST['user_name'])) {
            $this->feedback = "Empty Username";
        } elseif (empty($_POST['new_password']) || empty($_POST['new_password_repeat'])) {
            $this->feedback = "Empty Password";
        } elseif ($_POST['new_password'] !== $_POST['new_password_repeat']) {
            $this->feedback = "Password and password repeat are not the same";
        } elseif (strlen($_POST['new_password']) < 6) {
            $this->feedback = "Password has a minimum length of 6 characters";
        } elseif (strlen($_POST['user_name']) > 64 || strlen($_POST['user_name']) < 2) {
            $this->feedback = "Username cannot be shorter than 2 or longer than 64 characters";
        } elseif (!preg_match('/^[a-z\d]{2,64}$/i', $_POST['user_name'])) {
            $this->feedback = "Username does not fit the name scheme: only a-Z and numbers are allowed, 2 to 64 characters";
        } else {
            $this->feedback = "An unknown error occurred.";
        }
        return false;
    }

    private function changePassword() {
        $user_name = htmlentities($_POST['user_name'], ENT_QUOTES);
        $user_password = $_POST['new_password'];
        // Encrypt the user's password with the PHP 5.5's password_hash() function, results in a 60 char hash string.
        // the constant PASSWORD_DEFAULT comes from PHP 5.5 or the password_compatibility_library
        $user_password_hash = password_hash($user_password, PASSWORD_DEFAULT);
        $sql = 'UPDATE users SET user_password_hash = :user_password_hash WHERE user_name = :user_name';
        $query = $this->db_connection->prepare($sql);
        $query->bindValue(':user_name', $user_name);
        $query->bindValue(':user_password_hash', $user_password_hash);
        $change_success_state = $query->execute();
        if ($change_success_state) {
            if ($user_name == $_COOKIE['login_user']) $this->doLogout();
            $this->feedback = "Password change success. ";
            return true;
        } else {
            $this->feedback = "Password change failed. ";
        }
        return false;
    }

    private function changeRestriction() {
        $user_name = htmlentities($_POST['user_name'], ENT_QUOTES);
        $user_restriction = htmlentities($_POST['user_restriction'], ENT_QUOTES);
        $sql = 'UPDATE users SET user_restriction = :user_restriction WHERE user_name = :user_name';
        $query = $this->db_connection->prepare($sql);
        $query->bindValue(':user_name', $user_name);
        $query->bindValue(':user_restriction', $user_restriction);
        $change_success_state = $query->execute();
        if ($change_success_state) {
            $this->feedback = "Restriction change success. ";
            return true;
        } else {
            $this->feedback = "Restriction change failed. ";
        }
        return false;
    }

    private function changeTheme() {
        $user_name = htmlentities($_POST['user_name'], ENT_QUOTES);
        $user_theme = htmlentities($_POST['user_theme'], ENT_QUOTES);
        $sql = 'UPDATE users SET user_theme = :user_theme WHERE user_name = :user_name';
        $query = $this->db_connection->prepare($sql);
        $query->bindValue(':user_name', $user_name);
        $query->bindValue(':user_theme', $user_theme);
        $passchange_success_state = $query->execute();
        if ($passchange_success_state) {
            $this->feedback = "Theme change success. ";
            return true;
        } else {
            $this->feedback = "Theme chage failed. ";
        }
        return false;
    }

    private function checkDeleteUserData() {
        if (!empty($_POST['user_name'])
            && strlen($_POST['user_name']) <= 64
            && strlen($_POST['user_name']) >= 2
        ) {
            return true;
        } elseif (empty($_POST['user_name'])) {
            $this->feedback = "Empty Username";
        } elseif (strlen($_POST['user_name']) > 64 || strlen($_POST['user_name']) < 2) {
            $this->feedback = "Username cannot be shorter than 2 or longer than 64 characters";
        } elseif (!preg_match('/^[a-z\d]{2,64}$/i', $_POST['user_name'])) {
            $this->feedback = "Username does not fit the name scheme: only a-Z and numbers are allowed, 2 to 64 characters";
        } else {
            $this->feedback = "An unknown error occurred.";
        }
        return false;
    }

    private function deleteUser() {
        // remove html code etc. from username and email
        $user_name = htmlentities($_POST['user_name'], ENT_QUOTES);
        // crypt the user's password with the PHP 5.5's password_hash() function, results in a 60 char hash string.
        // the constant PASSWORD_DEFAULT comes from PHP 5.5 or the password_compatibility_library
        $user_password_hash = password_hash($user_password, PASSWORD_DEFAULT);

        $sql = 'DELETE FROM users WHERE user_name = :user_name';
        $query = $this->db_connection->prepare($sql);
        $query->bindValue(':user_name', $user_name);
        $deleteuser_success_state = $query->execute();

        if ($deleteuser_success_state) {
            $this->feedback = "Deleted user " . $user_name . ".";
            return true;
        } else {
            $this->feedback = "Delete user failed.";
        }
        // default return
        return false;
    }

    private function writeAuthLog($auth, $user) {
        $auth_file = getcwd() . "/../log/auth.log";
        $date = new DateTime();
        if ($auth == 2) $auth = 'NOUSER';
        else if ($auth == 1) $auth = 'LOGIN';
        else if ($auth == 0) $auth = 'NOPASS';
        $ip = $_SERVER['REMOTE_ADDR'];
        if (isset($_SERVER['REMOTE_HOST'])) $hostaddress = $_SERVER['REMOTE_HOST'];
        else $hostaddress = ' ';
        $referred = $_SERVER['HTTP_REFERER'];
        if ($referred == "") $referred = $auth_write . 'direct';
        $browser = $_SERVER['HTTP_USER_AGENT'];
        $auth_write = $date->format('Y m d H:i:s') . ', ' . $auth . ', ' . $user . ', ' . $ip . ', ' . $hostaddress . ', ' . $referred . ', ' . $browser . "\n";

        $fh = fopen($auth_file, 'a') or die("Error: Can't find/open " . $auth_file);
        fwrite($fh, $auth_write);
        fclose($fh);
    }

    // Login page
    private function showPageLoginForm() {
        $mycodo_db = "../config/mycodo.db";
        $db = new SQLite3($mycodo_db);
        if (isset($_POST['dismiss'])) {  // Dismiss Notification
            $stmt = $db->prepare("UPDATE Misc SET Dismiss_Notification=:dismiss");
            $stmt->bindValue(':dismiss', 1, SQLITE3_INTEGER);
            $stmt->execute();
        }
        $stmt = $db->query('SELECT Login_Message, Dismiss_Notification FROM Misc');
        while ($row = $stmt->fetchArray()) {
            $login_message = $row[0]; 
            $dismiss = $row[1];
        }
        ?>
        <html>
        <head>
            <link rel="icon" type="image/png" href="img/favicon.png">
        </head>
        <body>
        <div style="text-align: center;">
            <?php if ($this->feedback) echo $this->feedback . "<br/>"; ?>
        </div>
        <div style="padding-top: 1.5em; width: 100%; margin: 8 auto; text-align: center; ">
            <div style="padding-bottom: 0.6em; font-size: 1.8em;">Mycodo</div>
            <form method="post" action="<?php echo $_SERVER['SCRIPT_NAME']; ?>" name="loginform">
            <div style="padding: 0.2em;">
                <input style="width: 12em;" id="login_input_username" placeholder="User" type="text" name="user_name" title="Username or Email" required />
            </div>
            <div style="padding: 0.2em;">
                <input style="width: 12em;" id="login_input_password" placeholder="Password" type="password" name="user_password" autocomplete="off" required />
            </div>
            <div style="text-align: center; padding: 0.5em 0 1em 0;">
                <input type="checkbox" name="cookie" value="1"> Remember me (30 days)
            </div>
            <input type="submit"  name="login" value="Log in" />
            </form>
        </div>
        <?php
        if ($login_message != '') {
            echo '<div style="padding-top: 2em; width: 33em; margin: 8 auto; text-align: center;">' . $login_message . '</div>';
        }
        if (!$dismiss) {
            ?>
            <div style="padding-top: 1em; width: 33em; margin: 8 auto; text-align: justify;">
                <div style="padding: 1em 0 0.3em 0; text-align: center; font-size: 1.5em; font-weight: bold;">NO WARRANTY NOTICE</div>
                Mycodo is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
                <br>
                Mycodo is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
                <br>
                You should have received a copy of the GNU General Public License along with Mycodo. If not, see &lt;<a href="http://www.gnu.org/licenses/" target="_blank">http://www.gnu.org/licenses/</a>&gt;.
                <form method="post" action="<?php echo $_SERVER['SCRIPT_NAME']; ?>" name="dismiss">
                    <div style="text-align: center; padding-top:1em;">
                        <input type="hidden" name="dismiss" value="dismiss">
                        <input type="submit" name="dismiss" value="Dismiss Notice" />
                    </div>
                </form>
            </div>
            <?php
        }
        echo '</body></html>';
    }

    // Main page when logged in. What to display when the user is successfully authenticated.
    private function showPageLoggedIn() {
        require_once("includes/mycodo.php");
    }
}

// Run the application
$application = new OneFileLoginApplication();
