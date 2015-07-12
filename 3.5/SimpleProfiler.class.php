<?php
/**
 * A very simple php code profiler. No extensions required.
 *
 * Example usage:
 * <code>
 * declare(ticks=1);
 * require_once('./SimpleProfiler.class.php');
 * SimpleProfiler::start_profile();
 * // your code here
 * SimpleProfiler::stop_profile();
 * print_r(SimpleProfiler::get_profile());
 * </code>
 *
 * Consider combining with auto_prepend_file and auto_append_file
 *
 * @package SimpleProfiler
 * @author Kurt Payne
 * @copyright 2012 Go Daddy
 * @license http://www.gnu.org/licenses/gpl-3.0.txt GPLv3
 * @version Release: 1.0
 * @link http://inside.godaddy.com/write-code-profiler-php
 */
class SimpleProfiler {

    /**
     * Profile information
     * [file] => (
     *     [function] => runtime in microseconds
     * )
     * @access protected
     * @var array
     */
    protected static $_profile = array();

    /**
     * Remember the last time a tickable event was encountered
     * @access protected
     * @var float
     */
    protected static $_last_time = 0;

    /**
     * Return profile information
     * [file] => (
     *     [function] => runtime in microseconds
     * )
     * @access public
     * @return array
     */
    public static function get_profile() {
        return self::$_profile;
    }

    /**
     * Attempt to disable any detetected opcode caches / optimizers
     * @access public
     * @return void
     */
    public static function disable_opcode_cache() {
        if ( extension_loaded( 'xcache' ) ) {
            @ini_set( 'xcache.optimizer', false ); // Will be implemented in 2.0, here for future proofing
            // XCache seems to do some optimizing, anyway.
            // The recorded number of ticks is smaller with xcache.cacher enabled than without.
        } elseif ( extension_loaded( 'apc' ) ) {
            @ini_set( 'apc.optimization', 0 ); // Removed in APC 3.0.13 (2007-02-24)
            apc_clear_cache();
        } elseif ( extension_loaded( 'eaccelerator' ) ) {
            @ini_set( 'eaccelerator.optimizer', 0 );
            if ( function_exists( 'eaccelerator_optimizer' ) ) {
                @eaccelerator_optimizer( false );
            }
            // Try setting eaccelerator.optimizer = 0 in a .user.ini or .htaccess file
        } elseif (extension_loaded( 'Zend Optimizer+' ) ) {
            @ini_set('zend_optimizerplus.optimization_level', 0);
        }
    }

    /**
     * Start profiling
     * @access public
     * @return void
     */
    public static function start_profile() {
        if (0 === self::$_last_time) {
            self::$_last_time = microtime(true);
            self::disable_opcode_cache();
        }
        register_tick_function(array(__CLASS__, 'do_profile'));
    }

    /**
     * Stop profiling
     * @access public
     * @return void
     */
    public static function stop_profile() {
        unregister_tick_function(array(__CLASS__, 'do_profile'));
    }

    /**
     * Profile.
     * This records the source class / function / file of the current tickable event
     * and the time between now and the last tickable event. This information is
     * stored in self::$_profile
     * @access public
     * @return void
     */
    public static function do_profile() {

        // Get the backtrace, keep the object in case we need to reflect
        // upon it to find the original source file
        if ( version_compare( PHP_VERSION, '5.3.6' ) < 0 ) {
            $bt = debug_backtrace( true );
        } elseif ( version_compare( PHP_VERSION, '5.4.0' ) < 0 ) {
            $bt = debug_backtrace( DEBUG_BACKTRACE_IGNORE_ARGS | DEBUG_BACKTRACE_PROVIDE_OBJECT );
        } else {
            // Examine the last 2 frames
            $bt = debug_backtrace( DEBUG_BACKTRACE_IGNORE_ARGS | DEBUG_BACKTRACE_PROVIDE_OBJECT, 2 );
        }

        // Find the calling function $frame = $bt[0];
        if ( count( $bt ) >= 2 ) {
            $frame = $bt[1];
        }

        // If the calling function was a lambda, the original file is stored here.
        // Copy this elsewhere before unsetting the backtrace
        $lambda_file = @$bt[0]['file'];

        // Free up memory
        unset( $bt );

        // Include/require
        if ( in_array( strtolower( $frame['function'] ), array( 'include', 'require', 'include_once', 'require_once' ) ) ) {
            $file = $frame['args'][0];

        // Object instances
        } elseif ( isset( $frame['object'] ) && method_exists( $frame['object'], $frame['function'] ) ) {
            try {
                $reflector = new ReflectionMethod( $frame['object'], $frame['function'] );
                $file = $reflector->getFileName();
            } catch ( Exception $e ) {
            }

        // Static method calls
        } elseif ( isset( $frame['class'] ) && method_exists( $frame['class'], $frame['function'] ) ) {
            try {
                $reflector = new ReflectionMethod( $frame['class'], $frame['function'] );
                $file = $reflector->getFileName();
            } catch ( Exception $e ) {
            }

        // Functions
        } elseif ( !empty( $frame['function'] ) && function_exists( $frame['function'] ) ) {
            try {
                $reflector = new ReflectionFunction( $frame['function'] );
                $file = $reflector->getFileName();
            } catch ( Exception $e ) {
            }

        // Lambdas / closures
        } elseif ( '__lambda_func' == $frame['function'] || '{closure}' == $frame['function'] ) {
            $file = preg_replace( '/\(\d+\)\s+:\s+runtime-created function/', '', $lambda_file );

        // File info only
        } elseif ( isset( $frame['file'] ) ) {
            $file = $frame['file'];

        // If we get here, we have no idea where the call came from.
        // Assume it originated in the script the user requested.
        } else {
            $file = $_SERVER['SCRIPT_FILENAME'];
        }

        // Function
        $function = $frame['function'];
        if (isset($frame['object'])) {
            $function = get_class($frame['object']) . '::' . $function;
        }

        // Create the entry for the file
        if (!isset(self::$_profile[$file])) {
            self::$_profile[$file] = array();
        }

        // Create the entry for the function
        if (!isset(self::$_profile[$file][$function])) {
            self::$_profile[$file][$function] = 0;
        }

        // Record the call
        self::$_profile[$file][$function] += (microtime(true) - self::$_last_time);
        self::$_last_time = microtime(true);
    }
}
?>