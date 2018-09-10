var gulp         	= require('gulp');
var jshint       	= require('gulp-jshint');
var gulpif       	= require('gulp-if');
var minimist     	= require('minimist');
jshintXMLReporter 	= require('gulp-jshint-xml-file-reporter');
var config       	= require('../../config');


var options      = minimist(process.argv.slice(2), config.environment);


// lint javascript files in development
gulp.task('lint-js', function(callback) {
    return gulp.src(config.jslint.src)
    	.pipe(gulpif(options.env === config.environment.development, jshint()))
    	.pipe(gulpif(options.env === config.environment.development, jshint.reporter('jshint-stylish')))
    	.pipe(gulpif(options.env === config.environment.development, jshint.reporter(jshintXMLReporter)))
        .on('end', jshintXMLReporter.writeFile({
            format: config.jslint.options.format,
            filePath: config.jslint.options.filePath
        }));
});
