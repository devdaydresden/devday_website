var gulp         = require('gulp');
var scsslint     = require('gulp-scss-lint');
var gulpif       = require('gulp-if');
var minimist     = require('minimist');
var config       = require('../../config');


var options      = minimist(process.argv.slice(2), config.environment);


// lint sass files in development
gulp.task('lint-sass', function(callback) {
    return gulp.src(config.sasslint.src)
    	.pipe(gulpif(options.env === config.environment.development, scsslint({
    		'config': config.sasslint.options.config,
	        'maxBuffer': config.sasslint.options.maxBuffer,
	        'endless': config.sasslint.options.endless,
	        'reporterOutputFormat': config.sasslint.options.reporterOutputFormat,
	        'filePipeOutput': config.sasslint.options.filePipeOutput
    	})))
    	.pipe(gulpif(options.env === config.environment.development, gulp.dest(config.sasslint.dest)));
});