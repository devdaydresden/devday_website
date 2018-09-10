var gulp   = require('gulp');
var clean  = require('gulp-clean');
var config = require('../../config');

/**
 * Delete folders and files
 */
gulp.task('clean-dist', function(callback) {
  	return gulp.src(config.clean.srcDist)
		.pipe(clean(config.clean.options));
});

gulp.task('clean-dist-test', function(callback) {
  	return gulp.src(config.clean.srcTest)
		.pipe(clean(config.clean.options));
});
