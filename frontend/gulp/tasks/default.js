var gulp = require('gulp');
var runSequence = require('run-sequence');

/**
 * Run all tasks needed for a build in defined order
 */
gulp.task('default', function(callback) {
	runSequence(
		['jquery', 'js', 'sass', 'fonts', 'images'],
		'html',
		['lint-js', 'lint-sass'], callback);
});
