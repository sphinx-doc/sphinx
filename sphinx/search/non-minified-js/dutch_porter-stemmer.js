// Generated from dutch_porter.sbl by Snowball 3.0.1 - https://snowballstem.org/

/**@constructor*/
var DutchPorterStemmer = function() {
    var base = new BaseStemmer();

    /** @const */ var a_0 = [
        ["", -1, 6],
        ["\u00E1", 0, 1],
        ["\u00E4", 0, 1],
        ["\u00E9", 0, 2],
        ["\u00EB", 0, 2],
        ["\u00ED", 0, 3],
        ["\u00EF", 0, 3],
        ["\u00F3", 0, 4],
        ["\u00F6", 0, 4],
        ["\u00FA", 0, 5],
        ["\u00FC", 0, 5]
    ];

    /** @const */ var a_1 = [
        ["", -1, 3],
        ["I", 0, 2],
        ["Y", 0, 1]
    ];

    /** @const */ var a_2 = [
        ["dd", -1, -1],
        ["kk", -1, -1],
        ["tt", -1, -1]
    ];

    /** @const */ var a_3 = [
        ["ene", -1, 2],
        ["se", -1, 3],
        ["en", -1, 2],
        ["heden", 2, 1],
        ["s", -1, 3]
    ];

    /** @const */ var a_4 = [
        ["end", -1, 1],
        ["ig", -1, 2],
        ["ing", -1, 1],
        ["lijk", -1, 3],
        ["baar", -1, 4],
        ["bar", -1, 5]
    ];

    /** @const */ var a_5 = [
        ["aa", -1, -1],
        ["ee", -1, -1],
        ["oo", -1, -1],
        ["uu", -1, -1]
    ];

    /** @const */ var /** Array<int> */ g_v = [17, 65, 16, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 128];

    /** @const */ var /** Array<int> */ g_v_I = [1, 0, 0, 17, 65, 16, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 128];

    /** @const */ var /** Array<int> */ g_v_j = [17, 67, 16, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 128];

    var /** number */ I_x = 0;
    var /** number */ I_p2 = 0;
    var /** number */ I_p1 = 0;
    var /** boolean */ B_e_found = false;


    /** @return {boolean} */
    function r_prelude() {
        var /** number */ among_var;
        /** @const */ var /** number */ v_1 = base.cursor;
        while(true)
        {
            /** @const */ var /** number */ v_2 = base.cursor;
            lab0: {
                base.bra = base.cursor;
                among_var = base.find_among(a_0);
                base.ket = base.cursor;
                switch (among_var) {
                    case 1:
                        if (!base.slice_from("a"))
                        {
                            return false;
                        }
                        break;
                    case 2:
                        if (!base.slice_from("e"))
                        {
                            return false;
                        }
                        break;
                    case 3:
                        if (!base.slice_from("i"))
                        {
                            return false;
                        }
                        break;
                    case 4:
                        if (!base.slice_from("o"))
                        {
                            return false;
                        }
                        break;
                    case 5:
                        if (!base.slice_from("u"))
                        {
                            return false;
                        }
                        break;
                    case 6:
                        if (base.cursor >= base.limit)
                        {
                            break lab0;
                        }
                        base.cursor++;
                        break;
                }
                continue;
            }
            base.cursor = v_2;
            break;
        }
        base.cursor = v_1;
        /** @const */ var /** number */ v_3 = base.cursor;
        lab1: {
            base.bra = base.cursor;
            if (!(base.eq_s("y")))
            {
                base.cursor = v_3;
                break lab1;
            }
            base.ket = base.cursor;
            if (!base.slice_from("Y"))
            {
                return false;
            }
        }
        while(true)
        {
            /** @const */ var /** number */ v_4 = base.cursor;
            lab2: {
                if (!base.go_out_grouping(g_v, 97, 232))
                {
                    break lab2;
                }
                base.cursor++;
                /** @const */ var /** number */ v_5 = base.cursor;
                lab3: {
                    base.bra = base.cursor;
                    lab4: {
                        /** @const */ var /** number */ v_6 = base.cursor;
                        lab5: {
                            if (!(base.eq_s("i")))
                            {
                                break lab5;
                            }
                            base.ket = base.cursor;
                            /** @const */ var /** number */ v_7 = base.cursor;
                            lab6: {
                                if (!(base.in_grouping(g_v, 97, 232)))
                                {
                                    break lab6;
                                }
                                if (!base.slice_from("I"))
                                {
                                    return false;
                                }
                            }
                            base.cursor = v_7;
                            break lab4;
                        }
                        base.cursor = v_6;
                        if (!(base.eq_s("y")))
                        {
                            base.cursor = v_5;
                            break lab3;
                        }
                        base.ket = base.cursor;
                        if (!base.slice_from("Y"))
                        {
                            return false;
                        }
                    }
                }
                continue;
            }
            base.cursor = v_4;
            break;
        }
        return true;
    };

    /** @return {boolean} */
    function r_mark_regions() {
        I_p1 = base.limit;
        I_p2 = base.limit;
        /** @const */ var /** number */ v_1 = base.cursor;
        {
            /** @const */ var /** number */ c1 = base.cursor + 3;
            if (c1 > base.limit)
            {
                return false;
            }
            base.cursor = c1;
        }
        I_x = base.cursor;
        base.cursor = v_1;
        if (!base.go_out_grouping(g_v, 97, 232))
        {
            return false;
        }
        base.cursor++;
        if (!base.go_in_grouping(g_v, 97, 232))
        {
            return false;
        }
        base.cursor++;
        I_p1 = base.cursor;
        lab0: {
            if (I_p1 >= I_x)
            {
                break lab0;
            }
            I_p1 = I_x;
        }
        if (!base.go_out_grouping(g_v, 97, 232))
        {
            return false;
        }
        base.cursor++;
        if (!base.go_in_grouping(g_v, 97, 232))
        {
            return false;
        }
        base.cursor++;
        I_p2 = base.cursor;
        return true;
    };

    /** @return {boolean} */
    function r_postlude() {
        var /** number */ among_var;
        while(true)
        {
            /** @const */ var /** number */ v_1 = base.cursor;
            lab0: {
                base.bra = base.cursor;
                among_var = base.find_among(a_1);
                base.ket = base.cursor;
                switch (among_var) {
                    case 1:
                        if (!base.slice_from("y"))
                        {
                            return false;
                        }
                        break;
                    case 2:
                        if (!base.slice_from("i"))
                        {
                            return false;
                        }
                        break;
                    case 3:
                        if (base.cursor >= base.limit)
                        {
                            break lab0;
                        }
                        base.cursor++;
                        break;
                }
                continue;
            }
            base.cursor = v_1;
            break;
        }
        return true;
    };

    /** @return {boolean} */
    function r_R1() {
        return I_p1 <= base.cursor;
    };

    /** @return {boolean} */
    function r_R2() {
        return I_p2 <= base.cursor;
    };

    /** @return {boolean} */
    function r_undouble() {
        /** @const */ var /** number */ v_1 = base.limit - base.cursor;
        if (base.find_among_b(a_2) == 0)
        {
            return false;
        }
        base.cursor = base.limit - v_1;
        base.ket = base.cursor;
        if (base.cursor <= base.limit_backward)
        {
            return false;
        }
        base.cursor--;
        base.bra = base.cursor;
        if (!base.slice_del())
        {
            return false;
        }
        return true;
    };

    /** @return {boolean} */
    function r_e_ending() {
        B_e_found = false;
        base.ket = base.cursor;
        if (!(base.eq_s_b("e")))
        {
            return false;
        }
        base.bra = base.cursor;
        if (!r_R1())
        {
            return false;
        }
        /** @const */ var /** number */ v_1 = base.limit - base.cursor;
        if (!(base.out_grouping_b(g_v, 97, 232)))
        {
            return false;
        }
        base.cursor = base.limit - v_1;
        if (!base.slice_del())
        {
            return false;
        }
        B_e_found = true;
        if (!r_undouble())
        {
            return false;
        }
        return true;
    };

    /** @return {boolean} */
    function r_en_ending() {
        if (!r_R1())
        {
            return false;
        }
        /** @const */ var /** number */ v_1 = base.limit - base.cursor;
        if (!(base.out_grouping_b(g_v, 97, 232)))
        {
            return false;
        }
        base.cursor = base.limit - v_1;
        {
            /** @const */ var /** number */ v_2 = base.limit - base.cursor;
            lab0: {
                if (!(base.eq_s_b("gem")))
                {
                    break lab0;
                }
                return false;
            }
            base.cursor = base.limit - v_2;
        }
        if (!base.slice_del())
        {
            return false;
        }
        if (!r_undouble())
        {
            return false;
        }
        return true;
    };

    /** @return {boolean} */
    function r_standard_suffix() {
        var /** number */ among_var;
        /** @const */ var /** number */ v_1 = base.limit - base.cursor;
        lab0: {
            base.ket = base.cursor;
            among_var = base.find_among_b(a_3);
            if (among_var == 0)
            {
                break lab0;
            }
            base.bra = base.cursor;
            switch (among_var) {
                case 1:
                    if (!r_R1())
                    {
                        break lab0;
                    }
                    if (!base.slice_from("heid"))
                    {
                        return false;
                    }
                    break;
                case 2:
                    if (!r_en_ending())
                    {
                        break lab0;
                    }
                    break;
                case 3:
                    if (!r_R1())
                    {
                        break lab0;
                    }
                    if (!(base.out_grouping_b(g_v_j, 97, 232)))
                    {
                        break lab0;
                    }
                    if (!base.slice_del())
                    {
                        return false;
                    }
                    break;
            }
        }
        base.cursor = base.limit - v_1;
        /** @const */ var /** number */ v_2 = base.limit - base.cursor;
        r_e_ending();
        base.cursor = base.limit - v_2;
        /** @const */ var /** number */ v_3 = base.limit - base.cursor;
        lab1: {
            base.ket = base.cursor;
            if (!(base.eq_s_b("heid")))
            {
                break lab1;
            }
            base.bra = base.cursor;
            if (!r_R2())
            {
                break lab1;
            }
            {
                /** @const */ var /** number */ v_4 = base.limit - base.cursor;
                lab2: {
                    if (!(base.eq_s_b("c")))
                    {
                        break lab2;
                    }
                    break lab1;
                }
                base.cursor = base.limit - v_4;
            }
            if (!base.slice_del())
            {
                return false;
            }
            base.ket = base.cursor;
            if (!(base.eq_s_b("en")))
            {
                break lab1;
            }
            base.bra = base.cursor;
            if (!r_en_ending())
            {
                break lab1;
            }
        }
        base.cursor = base.limit - v_3;
        /** @const */ var /** number */ v_5 = base.limit - base.cursor;
        lab3: {
            base.ket = base.cursor;
            among_var = base.find_among_b(a_4);
            if (among_var == 0)
            {
                break lab3;
            }
            base.bra = base.cursor;
            switch (among_var) {
                case 1:
                    if (!r_R2())
                    {
                        break lab3;
                    }
                    if (!base.slice_del())
                    {
                        return false;
                    }
                    lab4: {
                        /** @const */ var /** number */ v_6 = base.limit - base.cursor;
                        lab5: {
                            base.ket = base.cursor;
                            if (!(base.eq_s_b("ig")))
                            {
                                break lab5;
                            }
                            base.bra = base.cursor;
                            if (!r_R2())
                            {
                                break lab5;
                            }
                            {
                                /** @const */ var /** number */ v_7 = base.limit - base.cursor;
                                lab6: {
                                    if (!(base.eq_s_b("e")))
                                    {
                                        break lab6;
                                    }
                                    break lab5;
                                }
                                base.cursor = base.limit - v_7;
                            }
                            if (!base.slice_del())
                            {
                                return false;
                            }
                            break lab4;
                        }
                        base.cursor = base.limit - v_6;
                        if (!r_undouble())
                        {
                            break lab3;
                        }
                    }
                    break;
                case 2:
                    if (!r_R2())
                    {
                        break lab3;
                    }
                    {
                        /** @const */ var /** number */ v_8 = base.limit - base.cursor;
                        lab7: {
                            if (!(base.eq_s_b("e")))
                            {
                                break lab7;
                            }
                            break lab3;
                        }
                        base.cursor = base.limit - v_8;
                    }
                    if (!base.slice_del())
                    {
                        return false;
                    }
                    break;
                case 3:
                    if (!r_R2())
                    {
                        break lab3;
                    }
                    if (!base.slice_del())
                    {
                        return false;
                    }
                    if (!r_e_ending())
                    {
                        break lab3;
                    }
                    break;
                case 4:
                    if (!r_R2())
                    {
                        break lab3;
                    }
                    if (!base.slice_del())
                    {
                        return false;
                    }
                    break;
                case 5:
                    if (!r_R2())
                    {
                        break lab3;
                    }
                    if (!B_e_found)
                    {
                        break lab3;
                    }
                    if (!base.slice_del())
                    {
                        return false;
                    }
                    break;
            }
        }
        base.cursor = base.limit - v_5;
        /** @const */ var /** number */ v_9 = base.limit - base.cursor;
        lab8: {
            if (!(base.out_grouping_b(g_v_I, 73, 232)))
            {
                break lab8;
            }
            /** @const */ var /** number */ v_10 = base.limit - base.cursor;
            if (base.find_among_b(a_5) == 0)
            {
                break lab8;
            }
            if (!(base.out_grouping_b(g_v, 97, 232)))
            {
                break lab8;
            }
            base.cursor = base.limit - v_10;
            base.ket = base.cursor;
            if (base.cursor <= base.limit_backward)
            {
                break lab8;
            }
            base.cursor--;
            base.bra = base.cursor;
            if (!base.slice_del())
            {
                return false;
            }
        }
        base.cursor = base.limit - v_9;
        return true;
    };

    this.stem = /** @return {boolean} */ function() {
        /** @const */ var /** number */ v_1 = base.cursor;
        r_prelude();
        base.cursor = v_1;
        /** @const */ var /** number */ v_2 = base.cursor;
        r_mark_regions();
        base.cursor = v_2;
        base.limit_backward = base.cursor; base.cursor = base.limit;
        r_standard_suffix();
        base.cursor = base.limit_backward;
        /** @const */ var /** number */ v_3 = base.cursor;
        r_postlude();
        base.cursor = v_3;
        return true;
    };

    /**@return{string}*/
    this['stemWord'] = function(/**string*/word) {
        base.setCurrent(word);
        this.stem();
        return base.getCurrent();
    };
};
