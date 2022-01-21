function instrument = open_instrument(name, uri)
% open_instrument Opens an instrument given its InstrumentKit URI.
%
% WARNING: this function can execute arbitrary Python code, so do *not*
% call for untrusted URIs.

    % We need to use py.eval, since using py.* directly doesn't work for
    % @classmethods. This presents two drawbacks: first, we need to manage
    % the Python globals() dict directly, and second, we need to do string
    % manipulation to make the line of source code to evaluate.

    % To manage globals() ourselves, we need to make a new dict() that we will
    % pass to py.eval.
    namespace = py.dict();

    % Next, py.eval doesn't respect MATLAB's import py.* command-form function.
    % Thus, we need to use the __import__  built-in function to return the module
    % object for InstrumentKit. We'll save it directly into our new namespace,
    % so that it becomes a global for the next py.eval. Recall that d{'x'} on the
    % MATLAB side corresponds to d['x'] on the Python side, for d a Python dict().
    namespace{'ik'} = py.eval('__import__("instruments")', namespace);

    % Finally, we're equipped to run the open_from_uri @classmethod. To do so,
    % we want to evaluate a line that looks like:
    %     ik.holzworth.Holzworth.HS9000.open_from_uri(r"serial:/dev/ttyUSB0")
    % We use r to cut down on accidental escaping errors, but importantly, this will
    % do *nothing* to cut down intentional abuse of eval.
    instrument = py.eval(['ik.' name '.open_from_uri(r"' uri '")'], namespace);

end
